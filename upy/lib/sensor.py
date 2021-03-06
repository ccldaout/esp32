# -*- coding: utf-8 -*-

import machine
import time

class HCSR04(object):

    def __init__(self, trig_pin_num, echo_pin_num):
        self._trig = machine.Pin(trig_pin_num, machine.Pin.OUT)
        self._echo = machine.Pin(echo_pin_num, machine.Pin.IN)
        self.tmo_us = int(0.5*1000*1000)
        self.coef_cm = 0.017

    def measure(self):
        self._trig.value(1)
        time.sleep(0.00001)	# 10us
        self._trig.value(0)

        us = machine.time_pulse_us(self._echo, 1, self.tmo_us)
        if us > 0:
            dist = float(self.coef_cm * us)
            return min(max(2.0, dist), 400.0)
        return None

class QTRxRC(object):

    def __init__(self):
        self._pins = []

    def add_sensor(self, pin_num, duration_us, timeout_us, threshold_us=None):
        if threshold_us is None:
            threshold_us = timeout_us
        self._pins.append((machine.Pin(pin_num), duration_us, timeout_us, threshold_us))

    def sense(self):
        for pin, dur_us, tmo_us, _ in self._pins:
            pin.init(machine.Pin.OUT, value=1)
            time.sleep_us(dur_us)
            pin.init(machine.Pin.IN)
            us = machine.time_pulse_us(pin, 1, tmo_us)
            pin.init(machine.Pin.OUT, value=0)
            yield us

    def sense_black(self):
        for pin, dur_us, tmo_us, thr_us in self._pins:
            pin.init(machine.Pin.OUT, value=1)
            time.sleep_us(dur_us)
            pin.init(machine.Pin.IN)
            us = machine.time_pulse_us(pin, 1, tmo_us)
            pin.init(machine.Pin.OUT, value=0)
            if us == -2:
                yield False
            elif us == -1:
                yield True
            else:
                yield (us >= thr_us)
