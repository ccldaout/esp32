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

#define BUFSIZE_b 128

typedef struct _airterm_t {
    int socket;
    esp_timer_handle_t timer;
    uint32_t s_size;
    char s_buff[BUFSIZE_b];
    char t_buff[BUFSIZE_b];
} _airterm_t;

STATIC _airterm_t *aterm;
STATIC SemaphoreHandle_t aterm_mutex;


STATIC void _debug(const char *s)
{
    mp_hal_stdout_tx_strn_x(s, strlen(s), false);
    mp_hal_stdout_tx_strn_x("\r\n", 2, false);
}


STATIC void _airterm_recv(int socket)
{
    char buf[64];

    int n = lwip_recv(socket, buf, sizeof(buf), MSG_DONTWAIT);
    if (n > 0) {
	mp_hal_stdin_rx_insert(buf, n);
    } else {
	if (n == 0 || errno != EWOULDBLOCK) {
	    mp_airterm_unregister();
	}
    }
}

STATIC void _airterm_send(int socket, const char *data, uint32_t size)
{
    while (size > 0) {
	int n = lwip_send(socket, data, size, 0);
	if (n < 0) {
	    mp_airterm_unregister();
	    return;
	}
	data += n;
	size -= n;
    }
}

STATIC void _airterm_flush(void)
{
    char *data1;
    uint32_t size1;
    int socket;

    (void)xSemaphoreTake(aterm_mutex, portTICK_PERIOD_MS);
    if (aterm == 0) {
	xSemaphoreGive(aterm_mutex);
	return;
    }
    data1 = aterm->t_buff;
    size1 = aterm->s_size;
    if (size1 != 0) {
	(void)memcpy(data1, aterm->s_buff, size1);
	aterm->s_size = 0;
	socket = aterm->socket;
    }
    xSemaphoreGive(aterm_mutex);

    if (size1 != 0)
	_airterm_send(socket, data1, size1);
}

STATIC void mp_airterm_push(const char *data2, uint32_t size2)
{
    char *data1;
    uint32_t size1;
    int socket;

    if (aterm == 0)
	return;

    (void)xSemaphoreTake(aterm_mutex, portTICK_PERIOD_MS);
    if (aterm == 0) {
	xSemaphoreGive(aterm_mutex);
	return;
    }
    data1 = aterm->t_buff;
    if (aterm->s_size + size2 > BUFSIZE_b) {
	uint32_t shift2 = BUFSIZE_b - aterm->s_size;
	(void)memcpy(data1, aterm->s_buff, aterm->s_size);
	(void)memcpy(data1+aterm->s_size, data2, shift2);
	aterm->s_size = size2 - shift2;
	(void)memcpy(aterm->s_buff, data2+shift2, aterm->s_size);
	size1 = BUFSIZE_b;
	socket = aterm->socket;
    } else {
	(void)memcpy(aterm->s_buff+aterm->s_size, data2, size2);
	aterm->s_size += size2;
	size1 = 0;
    }
    xSemaphoreGive(aterm_mutex);

    if (size1 != 0)
	_airterm_send(socket, data1, size1);
}

STATIC void mp_airterm_transmit(void *__void)
{
    if (aterm != 0) {
	int socket = aterm->socket;
	_airterm_flush();
	_airterm_recv(socket);
    }
}

bool mp_airterm_register(int socket)
{
    if (aterm != 0)
	return false;

    if ((aterm = malloc(sizeof(*aterm))) == 0)
	return false;

    if (aterm_mutex == 0)
	aterm_mutex = xSemaphoreCreateMutex();	/* lock */

    aterm->socket = socket;
    aterm->s_size = 0;

    int enable = 1;
    lwip_setsockopt(socket, IPPROTO_TCP, TCP_NODELAY, &enable, sizeof(enable));

    esp_timer_create_args_t args = {
	.callback = mp_airterm_transmit,
	.arg = 0,
	.dispatch_method = ESP_TIMER_TASK,
	.name = "airterm",
    };
    esp_timer_create(&args, &aterm->timer);
    esp_timer_start_periodic(aterm->timer, 50*1000);

    mp_hal_set_stdout_forwarder(mp_airterm_push);

    xSemaphoreGive(aterm_mutex);		/* unlock */
    return true;
}

void mp_airterm_unregister(void)
{
    if (aterm != 0) {
	(void)xSemaphoreTake(aterm_mutex, portTICK_PERIOD_MS);
	if (aterm) {
	    esp_timer_stop(aterm->timer);
	    esp_timer_delete(aterm->timer);
	    mp_hal_set_stdout_forwarder(0);
	    if (aterm->socket != -1)
		lwip_close(aterm->socket);
	    aterm->socket = -1;
	    free(aterm);
	    aterm = 0;
	}
	xSemaphoreGive(aterm_mutex);
    }
}
