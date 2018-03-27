/*
 * This file is part of the MicroPython project, http://micropython.org/
 *
 * The MIT License (MIT)
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
#include <stdint.h>
#include <string.h>

#include "py/objstr.h"
#include "py/runtime.h"
#include "py/stream.h"
#include "extmod/modgenstream.h"

#if MICROPY_PY_GENSTREAM

typedef struct _mp_obj_genstream_t {
    mp_obj_base_t base;
} mp_obj_genstream_t;

STATIC mp_obj_t genstream_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args) {
    //mp_arg_check_num(n_args, n_kw, 0, 0, false);
    mp_obj_genstream_t *o = m_new_obj(mp_obj_genstream_t);
    o->base.type = type;
    return  MP_OBJ_FROM_PTR(o);
}

STATIC mp_uint_t genstream_read(mp_obj_t self_in, void *buf, mp_uint_t size, int *errcode) {
    mp_obj_genstream_t *self =  MP_OBJ_TO_PTR(self_in);
    mp_obj_t meth[3];
    mp_load_method(self, MP_QSTR_read, meth);
    meth[2] = mp_obj_new_int(size);

    mp_obj_t ret;
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
	ret = mp_call_method_n_kw(1, 0, meth);
	nlr_pop();
    } else {
	*errcode = MP_EIO;
	return MP_STREAM_ERROR;
    }
    const char *data = mp_obj_str_get_data(ret, &size);
    (void)memcpy(buf, data, size);
    return size;
}

STATIC mp_uint_t genstream_write(mp_obj_t self_in, const void *buf, mp_uint_t size, int *errcode) {
    mp_obj_genstream_t *self =  MP_OBJ_TO_PTR(self_in);
    mp_obj_t meth[3];
    mp_load_method(self, MP_QSTR_write, meth);
    meth[2] = mp_obj_new_str_of_type(&mp_type_bytes, buf, size);

    mp_obj_t ret;
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
	ret = mp_call_method_n_kw(1, 0, meth);
	nlr_pop();
    } else {
	*errcode = MP_EIO;
	return MP_STREAM_ERROR;
    }
    return mp_obj_get_int(ret);
}

STATIC const mp_stream_p_t genstream_stream_p = {
    .read = genstream_read,
    .write = genstream_write,
};

STATIC const mp_obj_type_t genstream_type = {
    { &mp_type_type },
    .name = MP_QSTR_genstream,
    .make_new = genstream_make_new,
    .protocol = &genstream_stream_p,
};

STATIC const mp_rom_map_elem_t genstream_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_genstream) },
    { MP_ROM_QSTR(MP_QSTR_genstream), MP_ROM_PTR(&genstream_type) },
};

STATIC MP_DEFINE_CONST_DICT(genstream_module_globals, genstream_module_globals_table);

const mp_obj_module_t mp_module_genstream = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&genstream_module_globals,
};

#endif // MICROPY_PY_GENSTREAM
