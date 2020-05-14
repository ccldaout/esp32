import machine
import time

from sensor import QTRxRC

pins = (26, 27, 15)

sensor = QTRxRC(pins)

def test(cnt, time_us, tmo_us, itv_s):
    sensor.duration_us = time_us
    sensor.timeout_us = tmo_us

    def sensed():
        for v in sensor.sense():
            if v == -2:
                yield 'W'
            elif v == -1:
                yield 'B'
            else:
                yield '? (%d)' % v

    beg = time.time()
    for _ in range(cnt):
        print(tuple(sensed()))
        time.sleep(itv_s)
    ela = time.time() - beg
    print('avg sec', ela/cnt - itv_s)

# test(30, 50, 100, 0.2)
