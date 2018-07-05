# -*- coding: utf-8 -*-

import machine
from time import sleep

adc = machine.ADC(machine.Pin(35))

def meas(itv_s=0.1):
    while True:
        sleep(itv_s)
        print(adc.read())
