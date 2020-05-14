import math
import time
import servo

class Mounter(object):

    def __init__(self, h_pin_num, v_pin_num):
        self._hservo = servo.ServoSG90(h_pin_num)
        self._vservo = servo.ServoSG90(v_pin_num)
        
    def position(self, h_ang, v_ang):
        self._hservo.angle(h_ang)
        self._vservo.angle(v_ang)

H_PIN_NUM = 17
V_PIN_NUM = 13

mounter = Mounter(H_PIN_NUM, V_PIN_NUM)

def deg2rad(deg):
    return math.pi * (deg / 180.0)

class Sequence(object):

    def __init__(self, min_ang, max_ang):
        self._min = min_ang
        self._max = max_ang

    def refuse(self):
        yield (self._min, 0)
        yield (self._max, 0)
        yield (0, 0)

    def nod(self):
        yield (0, self._max)
        yield (0, self._min)
        yield (0, 0)

    def spiral(self, count, d_step, r_scale):
        yield (0, self._max)
        d = 90
        r = self._max
        d_max = d + 360*count
        while d < d_max:
            d += d_step
            r *= r_scale
            rad = deg2rad(d)
            yield (r*math.cos(rad), r*math.sin(rad))
        yield (0, 0)

def demo(count=3, ang_step=2, r_scale=1.0, sp_wait=0.003):
    seq = Sequence(-45, 45)

    for h, v in seq.refuse():
        mounter.position(h, v)
        time.sleep(0.4)

    for h, v in seq.spiral(count, ang_step, r_scale):
        mounter.position(h, v)
        time.sleep(sp_wait)

    for h, v in seq.nod():
        mounter.position(h, v)
        time.sleep(0.5)

demo()
print ('demo(count=3, ang_step=2, r_scale=1.0, sp_wait=0.003)')

