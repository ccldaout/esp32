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

#ifndef INCLUDED_MPHALPORT_ADD_H
#define INCLUDED_MPHALPORT_ADD_H

#include "py/obj.h"

void mp_hal_stdin_rx_insert(const char *data, mp_uint_t size);
void mp_hal_set_stdout_forwarder(void (*forwarder)(const char *, uint32_t));
void mp_hal_stdout_tx_str_x(const char *str, bool foward);
void mp_hal_stdout_tx_strn_x(const char *str, uint32_t len, bool forward);
void mp_hal_stdout_tx_strn_cooked_x(const char *str, uint32_t len, bool forward);

void mp_vterm_init(void);
bool mp_vterm_register_airterm(int socket);
bool mp_vterm_register_dupterm(void);
void mp_vterm_unregister(void);

#endif // INCLUDED_MPHALPORT_H
