# -*- coding: utf-8 -*-

import max32664
import time

def meas(itv_ms=250):
    
    mx = max32664.MAX32664()
    mx.init()

    from display import display as _disp

    while True:
        _disp.clear()
        bpm = mx.get()
        if bpm.status == 3:
            _disp.gcf_put(2, 2,  "  HR: %5.1f" % bpm.heart_rate)
            _disp.gcf_put(2, 20, "SpO2: %5.1f%%" % bpm.SpO2)
            _disp.gcf_put(2, 38, " CON: %3d%%" % bpm.confidence)
        time.sleep_ms(itv_ms)
