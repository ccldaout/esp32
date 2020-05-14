# -*- coding: utf-8 -*-

import machine
from time import sleep_ms, ticks_ms
from display import display as _disp

class PeakFinder(object):

    def __init__(self, h_width=6, raw_n=6, depth=100):
        self.__dv_h = h_width
        self.__raw_n = raw_n
        self.depth = depth
        self.callback = lambda t:None
        self.__sum = 0
        self.__dv = [0] * (h_width * 2 + 1)
        self.__rv = [0] * raw_n
        self.__sup_val = 0
        self.__sup_tms = 0
        self.__inf_val = 0
        self.__inf_tms = 0

    def update(self, new_tms, new_val):
        self.__sum -= self.__rv.pop(0)
        self.__rv.append(new_val)
        self.__sum += new_val
        dv = self.__dv
        hn = self.__dv_h
        dv.pop(0)
        avg = self.__sum / self.__raw_n
        dv.append(avg)
        mid = dv[hn]
        oth = dv[:hn] + dv[hn+1:]
        if mid > max(oth):
            if (self.__sup_tms and self.__inf_tms and
                (mid - self.__inf_val) > self.depth):
                self.callback(new_tms - self.__sup_tms)
            self.__sup_val, self.__sup_tms = mid, new_tms
            self.__inf_val, self.__inf_tms = 0, 0
        elif mid < min(oth):
            self.__inf_val, self.__inf_tms = mid, new_tms
        return avg

adc = machine.ADC(machine.Pin(35))

D_MIN = 1300
D_MAX = 1850
L_RGB = _disp.Color(0, (1<<6)-1, 0)

def meas(itv_ms=30):
    _disp.clear()
    updcnt = 0
    def found(tms):
        nonlocal updcnt
        updcnt += 1
        hc = 60000.0/tms
        hc_s = '%5.1f (%1d)' % (hc, updcnt)
        _disp.clear(5, 51, 95, 63)
        _disp.gcf_put(5, 51, hc_s)
    _disp.clear()
    pf = PeakFinder(int(300/itv_ms), 5)
    pf.callback = found
    og = 0
    while True:
        v = adc.read()
        v = pf.update(ticks_ms(), v)
        g = int(50 * (1 - ((v - D_MIN) / (D_MAX - D_MIN))))
        g = min(49, g)
        g = max( 0, g)
        _disp.copy(1, 0, 95, 50, 0, 0)
        sleep_ms(itv_ms)
        _disp.clear(95, 0, 95, 50)
        _disp.draw_line(94, og, 95, g, L_RGB)
        og = g
        print(v, g)
