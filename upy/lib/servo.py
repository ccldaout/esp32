import machine

class Spec(object):

    def __init__(self, *, freq, duty_bits, min_us, min_ang, max_us, max_ang):
        self.freq = freq
        self._lim_us = int(1.0/freq * 1000000)
        self._lim_duty = (1 << duty_bits)
        self._min_us = min_us
        self._min_ang = min_ang
        self._max_ang = max_ang
        self._range_us = max_us - min_us
        self._range_ang = max_ang - min_ang

    def duty_by_ang(self, ang):
        us = self._min_us + self._range_us * (ang - self._min_ang)/self._range_ang
        duty = self._lim_duty * (us / float(self._lim_us))
        return int(round(duty))

class Servo(object):

    def __init__(self, pin_num, spec, init_angle):
        self._pin_num = pin_num
        self._spec = spec
        self.duty_by_angle = spec.duty_by_ang	# for performance
        self.min_angle = self._spec._min_ang
        self.max_angle = self._spec._max_ang
        self._pwm = machine.PWM(machine.Pin(self._pin_num))
        self._pwm.freq(self._spec.freq)
        self.duty = self._pwm.duty		# for performance
        self.angle(init_angle)

    def angle(self, angle):
        self.duty(self.duty_by_angle(angle))

    def stop(self):
        self._pwm.deinit()
        self._pwm = None

    def restart(self):
        self._pwm = machine.PWM(machine.Pin(self._pin_num))
        self._pwm.freq(self._spec.freq)

def ServoSG90(pin_num, init_angle=0):
    spec = Spec(freq=50, duty_bits=10,
                min_us=500, min_ang=-90,
                max_us=2400, max_ang=90)
    return Servo(pin_num, spec, init_angle)
