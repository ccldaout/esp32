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
#include <string.h>
#include <sys/time.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "rom/uart.h"

#include "py/mpstate.h"
#include "py/mphal.h"
#include "extmod/misc.h"
#include "lib/utils/pyexec.h"

#include "driver/uart.h"
#include "mphalport_add.h"
#include "freertos/semphr.h"
#include "py/runtime.h"

STATIC uint8_t stdin_ringbuf_array[256];
ringbuf_t stdin_ringbuf = {stdin_ringbuf_array, sizeof(stdin_ringbuf_array)};

static void (*stdout_forwarder)(const char *data, uint32_t len);
STATIC SemaphoreHandle_t mutex_handle;

void mp_hal_set_stdout_forwarder(void (*forwarder)(const char *, uint32_t))
{
    if (mutex_handle == 0) {
	mutex_handle = xSemaphoreCreateMutex();
	if (mutex_handle)
	    xSemaphoreGive(mutex_handle);
    }
    stdout_forwarder = forwarder;
}

STATIC inline void sem_lock(void)
{
    if (mutex_handle) {
	(void)xSemaphoreTake(mutex_handle, portTICK_PERIOD_MS);
    }
}

STATIC inline void sem_unlock(void)
{
    if (mutex_handle) {
	xSemaphoreGive(mutex_handle);
    }
}

void mp_hal_stdin_rx_insert(const char *data, mp_uint_t size)	/* NEW */
{
    uart_disable_rx_intr(UART_NUM_0);
    sem_lock();
    for (; size; data++, size--) {
	ringbuf_put(&stdin_ringbuf, *data);
    }
    sem_unlock();
    uart_enable_rx_intr(UART_NUM_0);
}

int mp_hal_stdin_rx_chr(void) {
    for (;;) {
	sem_lock();
        int c = ringbuf_get(&stdin_ringbuf);
	sem_unlock();
        if (c != -1) {
            return c;
        }
        MICROPY_EVENT_POLL_HOOK
        vTaskDelay(1);
    }
}

STATIC void call_stdout_forwarder(const char *str, uint32_t len)
{
    void (*forwarder)(const char *, uint32_t) = stdout_forwarder;
    if (forwarder != 0) {
	forwarder(str, len);
    }
}

void mp_hal_stdout_tx_char(char c) {
    uart_tx_one_char(c);
    //mp_uos_dupterm_tx_strn(&c, 1);
}

void mp_hal_stdout_tx_str_x(const char *str, bool forward) {
    const char * const s = str;
    uint32_t n = strlen(s);
    MP_THREAD_GIL_EXIT();
    while (*str) {
        mp_hal_stdout_tx_char(*str++);
    }
    if (forward)
	call_stdout_forwarder(s, n);
    MP_THREAD_GIL_ENTER();
}

void mp_hal_stdout_tx_strn_x(const char *str, uint32_t len, bool forward) {
    const char * const s = str;
    const uint32_t n = len;
    MP_THREAD_GIL_EXIT();
    while (len--) {
        mp_hal_stdout_tx_char(*str++);
    }
    if (forward)
	call_stdout_forwarder(s, n);
    MP_THREAD_GIL_ENTER();
}

void mp_hal_stdout_tx_strn_cooked_x(const char *str, uint32_t len, bool forward) {
    char buff[64];
    char *p, *e = &buff[sizeof(buff)];

    if (stdout_forwarder == 0)
	forward = false;

    MP_THREAD_GIL_EXIT();
    p = buff;
    while (len--) {
        if (*str == '\n') {
	    if (forward) {
		if (p == e) {
		    call_stdout_forwarder(buff, sizeof(buff));
		    p = buff;
		}
		*p++ = '\r';
	    }
            mp_hal_stdout_tx_char('\r');
        }
	if (forward) {
	    if (p == e) {
		call_stdout_forwarder(buff, sizeof(buff));
		p = buff;
	    }
	    *p++ = *str;
	}
        mp_hal_stdout_tx_char(*str++);
    }
    if (forward)
	call_stdout_forwarder(buff, p - buff);
    MP_THREAD_GIL_ENTER();
}

void mp_hal_stdout_tx_str(const char *str) {
    mp_hal_stdout_tx_str_x(str, true);
}

void mp_hal_stdout_tx_strn(const char *str, uint32_t len) {
    mp_hal_stdout_tx_strn_x(str, len, true);
}

void mp_hal_stdout_tx_strn_cooked(const char *str, uint32_t len) {
    mp_hal_stdout_tx_strn_cooked_x(str, len, true);
}

uint32_t mp_hal_ticks_ms(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec * 1000 + tv.tv_usec / 1000;
}

uint32_t mp_hal_ticks_us(void) {
    struct timeval tv;
    gettimeofday(&tv, NULL);
    return tv.tv_sec * 1000000 + tv.tv_usec;
}

void mp_hal_delay_ms(uint32_t ms) {
    struct timeval tv_start;
    struct timeval tv_end;
    uint64_t dt;
    gettimeofday(&tv_start, NULL);
    for (;;) {
        gettimeofday(&tv_end, NULL);
        dt = (tv_end.tv_sec - tv_start.tv_sec) * 1000 + (tv_end.tv_usec - tv_start.tv_usec) / 1000;
        if (dt + portTICK_PERIOD_MS >= ms) {
            // doing a vTaskDelay would take us beyound requested delay time
            break;
        }
        MICROPY_EVENT_POLL_HOOK
        vTaskDelay(1);
    }
    if (dt < ms) {
        // do the remaining delay accurately
        ets_delay_us((ms - dt) * 1000);
    }
}

void mp_hal_delay_us(uint32_t us) {
    ets_delay_us(us);
}

// this function could do with improvements (eg use ets_delay_us)
void mp_hal_delay_us_fast(uint32_t us) {
    uint32_t delay = ets_get_cpu_frequency() / 19;
    while (--us) {
        for (volatile uint32_t i = delay; i; --i) {
        }
    }
}

/*
extern int mp_stream_errno;
int *__errno() {
    return &mp_stream_errno;
}
*/
