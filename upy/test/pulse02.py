# -*- coding: utf-8 -*-

import machine
from time import sleep_ms, ticks_ms
from display import display as _disp

class PeakFinder(object):

    def __init__(self, h_width=6, raw_n=6, depth=200):
        self.__dv_h = h_width
        self.__raw_n = raw_n
        self.depth = depth
        self.callback = lambda _:None
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
        dv.append(self.__sum / self.__raw_n)
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

adc = machine.ADC(machine.Pin(35))

def meas(itv_ms=25):
    _disp.clear()
    def found(tms):
        hc = 60000.0/tms
        hc_s = '%5.1f' % hc
        _disp.clear()
        _disp.gcf_put(5, 5, hc_s)
    pf = PeakFinder(int(300/itv_ms), 5)
    pf.callback = found
    while True:
        v = adc.read()
        pf.update(ticks_ms(), v)
        sleep_ms(itv_ms)
