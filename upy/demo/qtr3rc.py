import machine
import time

pins = (machine.Pin(26), machine.Pin(27), machine.Pin(15))

def check(time_us, tmo_us):
    for pin in pins:
        pin.init(machine.Pin.OUT, value=1)
        time.sleep_us(time_us)				# 50 us
        pin.init(machine.Pin.IN)
        yield machine.time_pulse_us(pin, 1, tmo_us)	# 100 us
        pin.init(machine.Pin.OUT, value=0)

def test(cnt, time_us, tmo_us, itv_s):
    beg = time.time()
    for _ in range(cnt):
        print(tuple(check(time_us, tmo_us)))
        time.sleep(itv_s)
    ela = time.time() - beg
    print('avg sec', ela/cnt - itv_s)

# test(30, 50, 100, 0.2)
