/*
 * This file is part of the MicroPython project, http://micropython.org/
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
#include "freertos/ringbuf.h"
#include "esp_timer.h"
#include "mphalport.h"
#include "lwip/sockets.h"
#include "py/nlr.h"
#include "py/builtin.h"
#include "py/runtime.h"
#include "py/stream.h"
#include "py/mpthread.h"

#include "vterm.h"

#define BUFSIZE_b 		128
#define PUSH_WAIT_tick		(1000 / portTICK_PERIOD_MS)
#define UNREG_WAIT_tick		(1000 / portTICK_PERIOD_MS)
#define RINGBUF_WAIT_tick	( 500 / portTICK_PERIOD_MS)
#define IO_INTERVAL_us		(20 * 1000)

typedef struct _vterm_ops_t {
    bool timered_read;
    bool buffered_write;
    ssize_t (*read)(void *vctx, void *buf, size_t n, bool in_gil);
    ssize_t (*write)(void *vctx, const void *buf, size_t n, bool in_gil);
    void (*unregister)(void *vctx);
} _vterm_ops_t;

typedef struct _vterm_t {
    void *vctx;
    bool timered_read;
    bool buffered_write;
    ssize_t (*read)(void *vctx, void *buf, size_t n, bool in_gil);
    ssize_t (*write)(void *vctx, const void *buf, size_t n, bool in_gil);
    void (*unregister)(void *vctx);
    esp_timer_handle_t timer;
    SemaphoreHandle_t mutex;
    char s_buff[BUFSIZE_b];
    size_t s_size;
} _vterm_t;


//----------------------------------------------------------------------------
//----------------------------------------------------------------------------

STATIC ssize_t _vterm_read_noop(void *vctx, void *buf, size_t n, bool in_gil)
{
    return -1;
}

STATIC ssize_t _vterm_write_noop(void *vctx, const void *buf, size_t n, bool in_gil)
{
    return -1;
}

STATIC void _vterm_unregister_noop(void *vctx)
{
}

STATIC _vterm_t vterm = {
    .read = _vterm_read_noop,
    .write = _vterm_write_noop,
    .unregister = _vterm_unregister_noop,
};

STATIC void _vterm_rx_chars(uint8_t *p, ssize_t n)
{
    for (; n--; p++) {
	if (*p == mp_interrupt_char) {
	    mp_keyboard_interrupt();
	} else if (xRingbufferSend(stdin_ringbuf, p, 1, RINGBUF_WAIT_tick) != pdTRUE) {
	    // drop input
	}
    }
}

STATIC void *__vterm_rx_thread(void *__in_gil)
{
    uint8_t buf[8];
    bool in_gil = (bool)__in_gil;
    for (;;) {
	nlr_buf_t nlr;
	if (nlr_push(&nlr) == 0) {
	    ssize_t n = vterm.read(vterm.vctx, buf, sizeof(buf), in_gil);
	    nlr_pop();
	    if (n > 0)
		_vterm_rx_chars(buf, n);
	    else if (n == -1)
		return 0;
	}
    }
}

STATIC mp_obj_t _vterm_rx_thread(void)
{
    (void)__vterm_rx_thread((void *)true);
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(_vterm_rx_thread_obj, _vterm_rx_thread);

STATIC void _vterm_rx_timered(bool in_gil)
{
    uint8_t buf[8];
    ssize_t n = vterm.read(vterm.vctx, buf, sizeof(buf), in_gil);
    if (n > 0)
	_vterm_rx_chars(buf, n);
    else if (n != -2)		// NOT TIMEOUT
	mp_vterm_unregister();
}

STATIC void _vterm_writeall(const char *data, uint32_t size, bool in_gil)
{
    while (size > 0) {
	int n = vterm.write(vterm.vctx, data, size, in_gil);
	if (n < 0) {
	    mp_vterm_unregister();
	    return;
	}
	data += n;
	size -= n;
    }
}

STATIC void mp_vterm_wr_direct(const char *data, uint32_t size)
{
    return _vterm_writeall(data, size, false);
}

STATIC void mp_vterm_wx_buffer(const char *data, uint32_t size)
{
    if (xSemaphoreTake(vterm.mutex, PUSH_WAIT_tick) == pdFALSE) {
	return;
    }
    if (vterm.s_size + size > BUFSIZE_b) {
	_vterm_writeall(vterm.s_buff, vterm.s_size, false);
	_vterm_writeall(data, size, false);
	vterm.s_size = 0;
    } else {
	(void)memcpy(&vterm.s_buff[vterm.s_size], data, size);
	vterm.s_size += size;
    }
    xSemaphoreGive(vterm.mutex);
}

STATIC void _vterm_flush(bool in_gil)
{
    if (xSemaphoreTake(vterm.mutex, 0) == pdTRUE) {
	if (vterm.s_size != 0) {
	    _vterm_writeall(vterm.s_buff, vterm.s_size, in_gil);
	    vterm.s_size = 0;
	}
	xSemaphoreGive(vterm.mutex);
    }
}

STATIC void mp_vterm_timered_io(void *__arg)
{
    if (vterm.buffered_write)
	_vterm_flush(false);
    if (vterm.timered_read)
	_vterm_rx_timered(false);
}

STATIC bool mp_vterm_register(void *vctx, const _vterm_ops_t *ops)
{
    vterm.vctx = vctx;
    vterm.timered_read = ops->timered_read;
    vterm.buffered_write = ops->buffered_write;
    vterm.write = ops->write;
    vterm.read = ops->read;
    vterm.unregister = ops->unregister;
    vterm.s_size = 0;

    if (vterm.mutex == 0) {
	return false;
    }

    if (vterm.buffered_write || vterm.timered_read) {
	if (vterm.timer == 0) {
	    return false;
	}
	if (esp_timer_start_periodic(vterm.timer, IO_INTERVAL_us) != ESP_OK) {
	    esp_timer_delete(vterm.timer);
	    vterm.timer = 0;
	    return false;
	}
    }

    if (!vterm.timered_read) {
	mp_obj_t mod = MP_OBJ_FROM_PTR(&mp_module_thread);
	mp_obj_t fun = mp_load_attr(mod, MP_QSTR_start_new_thread);
	mp_obj_t trg = MP_OBJ_FROM_PTR(&_vterm_rx_thread_obj);
	mp_obj_t args = mp_const_empty_tuple;
	nlr_buf_t nlr;
	if (nlr_push(&nlr) == 0) {
	    mp_call_function_2(fun, trg, args);
	    nlr_pop();
	} else {
	    if (vterm.buffered_write || vterm.timered_read)
		esp_timer_stop(vterm.timer);
	    return false;
	}
    }

    if (vterm.buffered_write)
	mp_hal_stdout_dup(mp_vterm_wx_buffer);
    else
	mp_hal_stdout_dup(mp_vterm_wr_direct);

    return true;
}

void mp_vterm_unregister(void)
{
    if (vterm.buffered_write || vterm.timered_read)
	esp_timer_stop(vterm.timer);

    bool do_unlock = true;
    if (xSemaphoreTake(vterm.mutex, UNREG_WAIT_tick) == pdFALSE) {
	do_unlock = false;
    }

    void (*unregister)(void *vctx) = vterm.unregister;
    vterm.read = _vterm_read_noop;
    vterm.write = _vterm_write_noop;
    vterm.unregister = _vterm_unregister_noop;
    mp_hal_stdout_dup(0);
    unregister(vterm.vctx);
    vterm.s_size = 0;

    if (do_unlock)
	xSemaphoreGive(vterm.mutex);
}

void mp_vterm_init(void)
{
    if (vterm.mutex == 0) {
	vterm.mutex = xSemaphoreCreateMutex();
	esp_timer_create_args_t args = {
	    .callback = mp_vterm_timered_io,
	    .arg = 0,
	    .dispatch_method = ESP_TIMER_TASK,
	    .name = "airterm",
	};
	esp_timer_create(&args, &vterm.timer);
    }
}

//----------------------------------------------------------------------------
//             airterm - LWIP socket level terminal duplication
//----------------------------------------------------------------------------

typedef struct _airterm_ctx_t {
    int socket;
} _airterm_ctx_t;

static _airterm_ctx_t airterm_ctx;

STATIC ssize_t airterm_read(void *__vctx, void *buf, size_t n, bool in_gil)
{
    _airterm_ctx_t *ctx = __vctx;
    ssize_t z = lwip_recvfrom_r(ctx->socket, buf, n, MSG_DONTWAIT, 0, 0);
    if (z == -1 && errno == EWOULDBLOCK)
	z = -2;
    return z;
}

STATIC ssize_t airterm_write(void *__vctx, const void *buf, size_t n, bool in_gil)
{
    _airterm_ctx_t *ctx = __vctx;
    if (in_gil)
	MP_THREAD_GIL_EXIT();
    ssize_t z = lwip_send_r(ctx->socket, buf, n, 0);
    if (in_gil)
	MP_THREAD_GIL_ENTER();
    return z;
}

STATIC void airterm_unregister(void *__vctx)
{
    _airterm_ctx_t *ctx = __vctx;
    if (ctx->socket != -1) {
	lwip_close_r(ctx->socket);
    }
    ctx->socket = -1;
}

bool mp_vterm_register_airterm(int socket)
{
    //int enable = 1;
    //lwip_setsockopt(socket, IPPROTO_TCP, TCP_NODELAY, &enable, sizeof(enable));
    airterm_ctx.socket = socket;

    _vterm_ops_t ops = {
	.timered_read = true,
	.buffered_write = true,
	.read = airterm_read,
	.write = airterm_write,
	.unregister = airterm_unregister,
    };

    return mp_vterm_register(&airterm_ctx, &ops);
}

//----------------------------------------------------------------------------
//              dupterm - altenative os.dupterm implementation
//----------------------------------------------------------------------------

typedef struct _dupterm_ctx_t {
    mp_obj_t stream;
} _dupterm_ctx_t;

static _dupterm_ctx_t dupterm_ctx;

STATIC ssize_t dupterm_read(void *__vctx, void *buf, size_t n, bool in_gil)
{
    _dupterm_ctx_t *ctx = __vctx;
    int flag = MP_STREAM_RW_READ|MP_STREAM_RW_ONCE;
    int errcode, z;
    if (!in_gil)
	MP_THREAD_GIL_ENTER();
    for (;;) {
	z = mp_stream_rw(ctx->stream, buf, 1, &errcode, flag);
	if (errcode != MP_EWOULDBLOCK)
	    break;
        vTaskDelay(20/portTICK_PERIOD_MS);
    }
    if (!in_gil)
	MP_THREAD_GIL_EXIT();
    if (errcode == 0)
	return z;
    return -1;
}

STATIC ssize_t dupterm_write(void *__vctx, const void *buf, size_t n, bool in_gil)
{
    _dupterm_ctx_t *ctx = __vctx;
    int errcode;
    size_t z;
    if (!in_gil)
	MP_THREAD_GIL_ENTER();
    z = mp_stream_rw(ctx->stream, (void *)buf, n, &errcode, MP_STREAM_RW_WRITE);
    if (!in_gil)
	MP_THREAD_GIL_EXIT();
    if (errcode == 0)
	return z;
    return -1;
}

STATIC void dupterm_unregister(void *__vctx)
{
    _dupterm_ctx_t *ctx = __vctx;
    (void)mp_stream_close(ctx->stream);
    ctx->stream = 0;
}

bool mp_vterm_register_dupterm(mp_obj_t stream, int __stacksize_b)
{
    _vterm_ops_t ops = {
	.timered_read = false,
	.buffered_write = true,
	.read = dupterm_read,
	.write = dupterm_write,
	.unregister = dupterm_unregister,
    };
    dupterm_ctx.stream = stream;
    return mp_vterm_register(&dupterm_ctx, &ops);
}
