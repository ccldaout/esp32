# -*- coding: utf-8 -*-

import max32664
from time import sleep_ms
from display import display as _disp

L_RGB = _disp.Color(0, (1<<6)-1, 0)

def meas(itv_ms=250):
    mx = max32664.MAX32664()
    mx.init()

    while True:
        _disp.clear()
        bpm = mx.get()
        if bpm.status != 3:
            continue
        _disp.gcf_put(2, 2,  "  HR: %5.1f" % bpm.heart_rate)
        _disp.gcf_put(2, 20, "SpO2: %5.1f%%" % bpm.SpO2)
        _disp.gcf_put(2, 38, " CON: %3d%%" % bpm.confidence)
        time.sleep_ms(itv_ms)
