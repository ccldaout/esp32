# -*- coding: utf-8 -*-

import max32664
import time

class Disp(object):

    def __init__(self):
        from display import display as d
        self._disp = d
        d.gcf_index = 1		# select LARGE font
        d.clear()
        d.gcf_bg_color = d.Color(0, 0, 0)
        xoff = 15
        d.gcf_put(xoff, 10, "  HR: ---.-", spacing=1)
        d.gcf_put(xoff, 25, "SpO2: ---.-%", spacing=1)
        d.gcf_put(xoff, 40, "conf: ---  %", spacing=1)
        self._xoff = xoff + (d.gcf_size[0] + 1) * 6

    def update(self, bpm):
        put = self._disp.gcf_put
        xoff = self._xoff
        if bpm.status == 3:
            put(xoff, 10,  "%5.1f" % bpm.heart_rate, spacing=1)
            put(xoff, 25, "%5.1f" % bpm.SpO2, spacing=1)
            put(xoff, 40, "%3d" % bpm.confidence, spacing=1)
        else:
            put(xoff, 10,  "---.-", spacing=1)
            put(xoff, 25, "---.-", spacing=1)
            put(xoff, 40, "---", spacing=1)


def meas(itv_ms=250):
    
    mx = max32664.MAX32664()
    mx.init()

    disp = Disp()

    while True:
        bpm = mx.get()
        disp.update(bpm)
        time.sleep_ms(itv_ms)
