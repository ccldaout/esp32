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

        self._tv_lim = time.ticks_ms()
        self._valid = False
        self._bpm = None

    def update(self, bpm):
        put = self._disp.gcf_put
        xoff = self._xoff
        tv_cur = time.ticks_ms()

        if bpm.status == 3:
            self._valid = True
            if self._bpm is None or bpm.heart_rate > 0.0:
                self._bpm = bpm

        if tv_cur > self._tv_lim:
            if self._valid:
                bpm = self._bpm
                put(xoff, 10,  "%5.1f" % bpm.heart_rate, spacing=1)
                put(xoff, 25, "%5.1f" % bpm.SpO2, spacing=1)
                put(xoff, 40, "%3d" % bpm.confidence, spacing=1)
            else:
                put(xoff, 10,  "---.-", spacing=1)
                put(xoff, 25, "---.-", spacing=1)
                put(xoff, 40, "---", spacing=1)
            self._valid = False
            self._tv_lim = tv_cur + 1000


def meas(itv_ms=50):
    
    def get(self):
        # Read sensor hub status
        #while True:
        #    self._cmd([0x00, 0x00])
        #    s, r = self._readreply()
        #    if s != 0:
        #        raise Exception('Unexpected read status: %d' % s)
        #    if (r & 0x1) != 0:
        #        raise Exception('Unexpceted Sensor HUB status: %d' % r)
        #    if (r & 0x8) != 0:
        #        break
        #    time.sleep_ms(10)

        ### Read # of samples available in the FIFO
        while True:
            self._cmd([0x12, 0x00])
            s, r = self._readreply()
            if r != 0:
                break
            time.sleep_ms(5)

        # Read data stored in output FIFO
        bpm_last = None
        for _ in range(r):
            self._cmd([0x12, 0x01])
            s, rv = self._readreply(6)
            bpm = max32664.BPM(rv)
            if bpm.status == 3 and bpm.heart_rate > 0.0:
                bpm_last = bpm
        return bpm_last if bpm_last is not None else bpm

    mx = max32664.MAX32664()
    mx.init()

    disp = Disp()

    while True:
        bpm = get(mx)		# bpm = mx.get()
        disp.update(bpm)
        time.sleep_ms(itv_ms)
