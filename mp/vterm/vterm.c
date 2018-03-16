/*
 * This file is part of the MicroPython project, http://micropython.org/
 *
 * Development of the code in this file was sponsored by Microbric Pty Ltd
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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "freertos/FreeRTOS.h"
#include "freertos/semphr.h"
#include "esp_timer.h"
#include "lwip/sockets.h"
#include "mphalport_add.h"

#define BUFSIZE_b 		128
#define PUSH_WAIT_tick		( 100 / portTICK_PERIOD_MS)
#define UNREG_WAIT_tick		(1000 / portTICK_PERIOD_MS)
#define IO_INTERVAL_us		(25 * 1000)

typedef struct _vterm_ops_t {
    ssize_t (*recv)(void *vctx, void *buf, size_t n);
    ssize_t (*send)(void *vctx, const void *buf, size_t n);
    void (*unregister)(void *vctx);
} _vterm_ops_t;

typedef struct _vterm_t {
    void *vctx;
    ssize_t (*recv)(void *vctx, void *buf, size_t n);
    ssize_t (*send)(void *vctx, const void *buf, size_t n);
    void (*unregister)(void *vctx);
    esp_timer_handle_t timer;
    SemaphoreHandle_t mutex;
    char s_buff[BUFSIZE_b];
    size_t s_size;
} _vterm_t;

STATIC void _debug(const char *s)
{
    mp_hal_stdout_tx_strn_x(s, strlen(s), false);
    mp_hal_stdout_tx_strn_x("\r\n", 2, false);
}

//----------------------------------------------------------------------------
//----------------------------------------------------------------------------

STATIC ssize_t _vterm_recv_noop(void *vctx, void *buf, size_t n)
{
    return 0;
}

STATIC ssize_t _vterm_send_noop(void *vctx, const void *buf, size_t n)
{
    return -1;
}

STATIC void _vterm_unregister_noop(void *vctx)
{
    
}

STATIC _vterm_t vterm = {
    .recv = _vterm_recv_noop,
    .send = _vterm_send_noop,
    .unregister = _vterm_unregister_noop,
};

STATIC void _vterm_recv(void)
{
    char buf[64];
    int ret;
    ssize_t (*recv)(void *vctx, void *buf, size_t n);

    ret = xSemaphoreTake(vterm.mutex, 1);
    recv = vterm.recv;
    if (ret == pdTRUE)
	xSemaphoreGive(vterm.mutex);

    int n = recv(vterm.vctx, buf, sizeof(buf));
    if (n > 0) {
	mp_hal_stdin_rx_insert(buf, n);
    } else {
	if (n == 0 || errno != EWOULDBLOCK) {
	    mp_vterm_unregister();
	}
    }
}

STATIC void _vterm_send(const char *data, uint32_t size)
{
    while (size > 0) {
	int n = vterm.send(vterm.vctx, data, size);
	if (n < 0) {
	    mp_vterm_unregister();
	    return;
	}
	data += n;
	size -= n;
    }
}

STATIC void _vterm_flush(void)
{
    if (xSemaphoreTake(vterm.mutex, 1) == pdTRUE) {
	if (vterm.s_size != 0) {
	    _vterm_send(vterm.s_buff, vterm.s_size);
	    vterm.s_size = 0;
	}
	xSemaphoreGive(vterm.mutex);
    }
}

STATIC void mp_vterm_push(const char *data, uint32_t size)
{
    if (xSemaphoreTake(vterm.mutex, PUSH_WAIT_tick) == pdFALSE) {
	_debug("mp_vterm_push: mutex timeout");
	return;
    }
    if (vterm.s_size + size > BUFSIZE_b) {
	_vterm_send(vterm.s_buff, vterm.s_size);
	_vterm_send(data, size);
	vterm.s_size = 0;
    } else {
	(void)memcpy(&vterm.s_buff[vterm.s_size], data, size);
	vterm.s_size += size;
    }
    xSemaphoreGive(vterm.mutex);
}

STATIC void mp_vterm_transmit(void *__arg)
{
    _vterm_flush();
    _vterm_recv();
}

STATIC bool mp_vterm_register(void *vctx, const _vterm_ops_t *ops)
{
    vterm.vctx = vctx;
    vterm.send = ops->send;
    vterm.recv = ops->recv;
    vterm.unregister = ops->unregister;
    vterm.s_size = 0;

    if (vterm.mutex == 0) {
	_debug("mp_vterm_register ... no mutex");
	return false;
    }
    if (vterm.timer == 0) {
	_debug("mp_vterm_register ... no timer");
	return false;
    }
    if (esp_timer_start_periodic(vterm.timer, IO_INTERVAL_us) != ESP_OK) {
	_debug("mp_vterm_register ... cannot start timer");
	esp_timer_delete(vterm.timer);
	vterm.timer = 0;
	return false;
    }

    mp_hal_set_stdout_forwarder(mp_vterm_push);

    return true;
}

void mp_vterm_unregister(void)
{
    _debug("mp_vterm_unregister");

    esp_timer_stop(vterm.timer);

    bool do_unlock = true;
    if (xSemaphoreTake(vterm.mutex, UNREG_WAIT_tick) == pdFALSE) {
	_debug("mp_vterm_unregister: mutex timeout");
	do_unlock = false;
    }

    void (*unregister)(void *vctx) = vterm.unregister;
    void *vctx = vterm.vctx;
    vterm.recv = _vterm_recv_noop;
    vterm.send = _vterm_send_noop;
    vterm.unregister = _vterm_unregister_noop;
    vterm.vctx = 0;
    vterm.s_size = 0;
    mp_hal_set_stdout_forwarder(0);
    unregister(vctx);

    if (do_unlock)
	xSemaphoreGive(vterm.mutex);
}

void mp_vterm_init(void)
{
    if (vterm.mutex == 0) {
	vterm.mutex = xSemaphoreCreateMutex();
	esp_timer_create_args_t args = {
	    .callback = mp_vterm_transmit,
	    .arg = 0,
	    .dispatch_method = ESP_TIMER_TASK,
	    .name = "airterm",
	};
	esp_timer_create(&args, &vterm.timer);
    }
}

//----------------------------------------------------------------------------
//----------------------------------------------------------------------------

typedef struct _aterm_ctx_t {
    int socket;
} _aterm_ctx_t;

static _aterm_ctx_t aterm_ctx;

STATIC ssize_t aterm_recv(void *__vctx, void *buf, size_t n)
{
    _aterm_ctx_t *ctx = __vctx;
    return lwip_recv(ctx->socket, buf, n, MSG_DONTWAIT);
}

STATIC ssize_t aterm_send(void *__vctx, const void *buf, size_t n)
{
    _aterm_ctx_t *ctx = __vctx;
    return lwip_send(ctx->socket, buf, n, 0);
}

STATIC void aterm_unregister(void *__vctx)
{
    _aterm_ctx_t *ctx = __vctx;
    if (ctx->socket != -1)
	lwip_close(ctx->socket);
    ctx->socket = -1;
}

bool mp_vterm_register_airterm(int socket)
{
    int enable = 1;
    aterm_ctx.socket = socket;
    lwip_setsockopt(socket, IPPROTO_TCP, TCP_NODELAY, &enable, sizeof(enable));

    _vterm_ops_t ops = {
	.recv = aterm_recv,
	.send = aterm_send,
	.unregister = aterm_unregister,
    };

    return mp_vterm_register(&aterm_ctx, &ops);
}

//----------------------------------------------------------------------------
//----------------------------------------------------------------------------

#if MICROPY_PY_OS_DUPTERM

STATIC ssize_t dupterm_recv(void *__vctx, void *buf, size_t n)
{
    int ch = mp_uos_dupterm_rx_chr();
    *(char *)buf = ch;
    return 1
}

STATIC ssize_t dupterm_send(void *__vctx, const void *buf, size_t n);
{
    mp_uos_dupterm_tx_strn(buf, n);
    return n;
}

STATIC void dupterm_unregister(void *__vctx)
{
    mp_uos_deactivate(0, "", MP_OBJ_NULL);
}

bool mp_vterm_register_dupterm(void)
{
    _vterm_ops_t ops = {
	.recv = dupterm_recv,
	.send = dupterm_send,
	.unregister = dupterm_unregister,
    };

    return mp_vterm_register(0, &ops);
}

#endif
