/*
 * This file is part of the MicroPython project, http://micropython.org/
 *
 * The MIT License (MIT)
 *
 * Copyright (c) 2014 Damien P. George
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included in
 * all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 * THE SOFTWARE.
 */

#include "py/mpconfig.h"
#if MICROPY_PY_MPOLL

#include <stdio.h>
#include <string.h>

#include "py/runtime.h"
#include "py/obj.h"
#include "py/objlist.h"
#include "py/stream.h"
#include "py/mperrno.h"
#include "py/mphal.h"

#include "lwip/sockets.h"

#include "modsocket.h"

// Flags for poll()
#define FLAG_ONESHOT (1)

/// \class Poll - poll class

//LWIP_SOCKET_OFFSET
//CONFIG_LWIP_MAX_SOCKETS

typedef struct _mp_obj_mpoll_t {
    mp_obj_base_t base;
    fd_set rset;
    fd_set wset;
    fd_set rset_result;
    fd_set wset_result;
    socket_obj_t *socks[CONFIG_LWIP_MAX_SOCKETS];
    int maxfd;
    //short iter_cnt;
    short iter_idx;
    int flags;
    // callee-owned tuple
    mp_obj_t ret_tuple;
} mp_obj_mpoll_t;

/// \method register(obj[, eventmask])
STATIC mp_obj_t poll_register(uint n_args, const mp_obj_t *args) {
    mp_obj_mpoll_t *self = args[0];
    mp_uint_t flags;
    if (n_args == 3) {
        flags = mp_obj_get_int(args[2]);
    } else {
        flags = MP_STREAM_POLL_RD | MP_STREAM_POLL_WR;
    }
    socket_obj_t *socket = MP_OBJ_TO_PTR(args[1]);	// [TODO] CHECK TYPE
    if ((flags & MP_STREAM_POLL_RD) != 0)
	FD_SET(socket->fd, &self->rset);
    if ((flags & MP_STREAM_POLL_WR) != 0)
	FD_SET(socket->fd, &self->wset);
    self->socks[socket->fd - LWIP_SOCKET_OFFSET] = socket;
    if (socket->fd > self->maxfd)
	self->maxfd = socket->fd;
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(mpoll_register_obj, 2, 3, poll_register);

/// \method unregister(obj)
STATIC mp_obj_t poll_unregister(mp_obj_t self_in, mp_obj_t obj_in) {
    mp_obj_mpoll_t *self = self_in;
    socket_obj_t *socket = MP_OBJ_TO_PTR(obj_in);	// [TODO] CHECK TYPE
    if (self->socks[socket->fd - LWIP_SOCKET_OFFSET] == NULL)
	return mp_const_none;				// [TODO] raise KeyError
    FD_CLR(socket->fd, &self->rset);
    FD_CLR(socket->fd, &self->wset);
    self->socks[socket->fd - LWIP_SOCKET_OFFSET] = NULL;
    if (socket->fd == self->maxfd) {
	int i;
	for (i = self->maxfd - 1; i >= LWIP_SOCKET_OFFSET; i--) {
	    if (self->socks[i - LWIP_SOCKET_OFFSET] != NULL)
		break;
	}
	self->maxfd = i;
    }
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_2(mpoll_unregister_obj, poll_unregister);

/// \method modify(obj, eventmask)
STATIC mp_obj_t poll_modify(mp_obj_t self_in, mp_obj_t obj_in, mp_obj_t eventmask_in) {
    mp_obj_mpoll_t *self = self_in;
    socket_obj_t *socket = MP_OBJ_TO_PTR(obj_in);	// [TODO] CHECK TYPE
    mp_uint_t flags = mp_obj_get_int(eventmask_in);
    if (self->socks[socket->fd - LWIP_SOCKET_OFFSET] != NULL) {
	FD_CLR(socket->fd, &self->rset);
	FD_CLR(socket->fd, &self->wset);
	if ((flags & MP_STREAM_POLL_RD) != 0)
	    FD_SET(socket->fd, &self->rset);
	if ((flags & MP_STREAM_POLL_WR) != 0)
	    FD_SET(socket->fd, &self->wset);
    } else
	;						// [TODO] rais KeyError
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_3(mpoll_modify_obj, poll_modify);

STATIC void remove_invalids(mp_obj_mpoll_t *self)
{
    fd_set testset;
    struct timeval testtmo = {.tv_sec=0, .tv_usec=0};
    FD_ZERO(&testset);
    for (int i = 0; i < CONFIG_LWIP_MAX_SOCKETS; i++) {
	if (self->socks[i] == NULL)
	    continue;
	int fd = i + LWIP_SOCKET_OFFSET;
	FD_SET(fd, &testset);
	if (lwip_select(fd+1, &testset, NULL, NULL, &testtmo) == -1) {
	    FD_CLR(fd, &self->rset);
	    FD_CLR(fd, &self->wset);
	    self->socks[i] = NULL;
	}
    }
}

STATIC int get_delay_ms(const struct timeval *target, int delay_ms)
{
    struct timeval now, trg = *target;
    (void)gettimeofday(&now, NULL);
    
    trg.tv_sec -= now.tv_sec;
    if (trg.tv_usec < now.tv_usec) {
	trg.tv_sec--;
	trg.tv_usec += 1000000;
    }
    trg.tv_usec -= now.tv_usec;
    int diff_ms = now.tv_sec*1000 + now.tv_usec/1000;
    if (diff_ms < 0)
	return 0;
    return (diff_ms > delay_ms) ? delay_ms : diff_ms;
}

STATIC mp_uint_t poll_poll_internal(uint n_args, const mp_obj_t *args) {
    mp_obj_mpoll_t *self = args[0];
    struct timeval timeout;
    struct timeval target_time;
    bool in_main = mp_thread_is_main();
    const int interval_ms = 20;

    // work out timeout (its given already in ms)
    mp_uint_t timeout_ms = -1;
    self->flags = 0;
    if (n_args >= 2) {
        if (args[1] != mp_const_none)
	    timeout_ms = mp_obj_get_int(args[1]);
        if (n_args >= 3)
            self->flags = mp_obj_get_int(args[2]);
    }

    if (timeout_ms > 0) {
	(void)gettimeofday(&target_time, NULL);
	target_time.tv_sec += (timeout_ms / 1000);
	target_time.tv_usec += (timeout_ms % 1000) * 1000;
	if (target_time.tv_usec >= 1000000) {
	    target_time.tv_usec -= 1000000;
	    target_time.tv_sec += 1;
	}
    }

    for (;;) {
	int nready;
	int delay_ms = timeout_ms == 0 ? 0 : get_delay_ms(&target_time, interval_ms);
	if (self->maxfd == LWIP_SOCKET_OFFSET - 1) {
	    vTaskDelay(delay_ms / portTICK_PERIOD_MS);
	    nready = 0;
	} else {
	    timeout.tv_sec = 0;
	    timeout.tv_usec = delay_ms * 1000;
	    self->rset_result = self->rset;
	    self->wset_result = self->wset;
	    nready = lwip_select(self->maxfd+1, &self->rset_result, &self->wset_result, NULL, &timeout);
	}
	if (nready > 0)
	    return nready;
	if (nready == 0) {
	    if (delay_ms < interval_ms)
		return 0;
	} else
	    remove_invalids(self);
	if (in_main) {
	    MP_THREAD_GIL_ENTER();
	    mp_handle_pending();
	    MP_THREAD_GIL_EXIT();
	}
    }
}

STATIC mp_obj_t poll_poll(uint n_args, const mp_obj_t *args) {
    mp_obj_mpoll_t *self = args[0];
    MP_THREAD_GIL_EXIT();
    mp_uint_t n_ready = poll_poll_internal(n_args, args);
    MP_THREAD_GIL_ENTER();

    // one or more objects are ready, or we had a timeout
    mp_obj_list_t *ret_list = mp_obj_new_list(n_ready, NULL);
    n_ready = 0;
    for (int i = 0; i < CONFIG_LWIP_MAX_SOCKETS; i++) {
	if (self->socks[i] == NULL)
	    continue;
	int fd = i + LWIP_SOCKET_OFFSET;
	int flags = 0;
	if (FD_ISSET(fd, &self->rset_result))
	    flags |= MP_STREAM_POLL_RD;
	if (FD_ISSET(fd, &self->wset_result))
	    flags |= MP_STREAM_POLL_WR;
	if (flags == 0)
	    continue;
	mp_obj_t tuple[2] = {MP_OBJ_FROM_PTR(self->socks[i]), MP_OBJ_NEW_SMALL_INT(flags)};
	ret_list->items[n_ready++] = mp_obj_new_tuple(2, tuple);
	if (self->flags & FLAG_ONESHOT) {
	    // Don't poll next time, until new event flags will be set explicitly
	    FD_CLR(fd, &self->rset);
	    FD_CLR(fd, &self->wset);
        }
    }
    return ret_list;
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(mpoll_poll_obj, 1, 3, poll_poll);

STATIC mp_obj_t poll_ipoll(size_t n_args, const mp_obj_t *args) {
    mp_obj_mpoll_t *self = MP_OBJ_TO_PTR(args[0]);

    if (self->ret_tuple == MP_OBJ_NULL) {
        self->ret_tuple = mp_obj_new_tuple(2, NULL);
    }

    MP_THREAD_GIL_EXIT();
    if (poll_poll_internal(n_args, args) == 0)
	self->iter_idx = CONFIG_LWIP_MAX_SOCKETS;
    else
	self->iter_idx = 0;
    MP_THREAD_GIL_ENTER();

    return args[0];
}
MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(mpoll_ipoll_obj, 1, 3, poll_ipoll);

STATIC mp_obj_t poll_iternext(mp_obj_t self_in) {
    mp_obj_mpoll_t *self = MP_OBJ_TO_PTR(self_in);

    while (self->iter_idx < CONFIG_LWIP_MAX_SOCKETS) {
	int i = self->iter_idx++;
	if (self->socks[i] == NULL)
	    continue;
	int fd = i + LWIP_SOCKET_OFFSET;
	int flags = 0;
	if (FD_ISSET(fd, &self->rset_result))
	    flags |= MP_STREAM_POLL_RD;
	if (FD_ISSET(fd, &self->wset_result))
	    flags |= MP_STREAM_POLL_WR;
	if (flags == 0)
	    continue;
	mp_obj_tuple_t *t = MP_OBJ_TO_PTR(self->ret_tuple);
	t->items[0] = MP_OBJ_FROM_PTR(self->socks[i]);
	t->items[1] = MP_OBJ_NEW_SMALL_INT(flags);
	if (self->flags & FLAG_ONESHOT) {
	    // Don't poll next time, until new event flags will be set explicitly
	    FD_CLR(fd, &self->rset);
	    FD_CLR(fd, &self->wset);
        }
	return MP_OBJ_FROM_PTR(t);
    }

    return MP_OBJ_STOP_ITERATION;
}

STATIC const mp_rom_map_elem_t poll_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_register), MP_ROM_PTR(&mpoll_register_obj) },
    { MP_ROM_QSTR(MP_QSTR_unregister), MP_ROM_PTR(&mpoll_unregister_obj) },
    { MP_ROM_QSTR(MP_QSTR_modify), MP_ROM_PTR(&mpoll_modify_obj) },
    { MP_ROM_QSTR(MP_QSTR_poll), MP_ROM_PTR(&mpoll_poll_obj) },
    { MP_ROM_QSTR(MP_QSTR_ipoll), MP_ROM_PTR(&mpoll_ipoll_obj) },
};
STATIC MP_DEFINE_CONST_DICT(poll_locals_dict, poll_locals_dict_table);

STATIC const mp_obj_type_t mp_type_poll = {
    { &mp_type_type },
    .name = MP_QSTR_poll,
    .getiter = mp_identity_getiter,
    .iternext = poll_iternext,
    .locals_dict = (void*)&poll_locals_dict,
};

/// \function poll()
STATIC mp_obj_t mpoll_poll(void) {
    mp_obj_mpoll_t *poll = m_new_obj(mp_obj_mpoll_t);
    poll->base.type = &mp_type_poll;
    poll->ret_tuple = MP_OBJ_NULL;
    FD_ZERO(&poll->rset);
    FD_ZERO(&poll->wset);
    poll->maxfd = LWIP_SOCKET_OFFSET - 1;
    for (int i = 0; i < CONFIG_LWIP_MAX_SOCKETS; i++)
	poll->socks[i] = NULL;
    return poll;
}
MP_DEFINE_CONST_FUN_OBJ_0(mp_mpoll_poll_obj, mpoll_poll);

STATIC const mp_rom_map_elem_t mp_module_mpoll_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_mpoll) },
    { MP_ROM_QSTR(MP_QSTR_poll), MP_ROM_PTR(&mp_mpoll_poll_obj) },
    { MP_ROM_QSTR(MP_QSTR_POLLIN), MP_ROM_INT(MP_STREAM_POLL_RD) },
    { MP_ROM_QSTR(MP_QSTR_POLLOUT), MP_ROM_INT(MP_STREAM_POLL_WR) },
    { MP_ROM_QSTR(MP_QSTR_POLLERR), MP_ROM_INT(MP_STREAM_POLL_ERR) },
    { MP_ROM_QSTR(MP_QSTR_POLLHUP), MP_ROM_INT(MP_STREAM_POLL_HUP) },
};

STATIC MP_DEFINE_CONST_DICT(mp_module_mpoll_globals, mp_module_mpoll_globals_table);

const mp_obj_module_t mp_module_mpoll = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&mp_module_mpoll_globals,
};

#endif // MICROPY_PY_MPOLL
