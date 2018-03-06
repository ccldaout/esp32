import machine

class DRV8835(object):

    MODE_IN_IN = 0	# MODE pin is LOW
    MODE_PH_EN = 1	# MODE pin is HIGH
    PWM_MAX_DUTY = 1023
    PWM_MAX_FREQ = 1000

    def __init__(self, mode, a_in1, a_in2, b_in1, b_in2):
        if mode == self.MODE_IN_IN:
            raise NotImplementedError()
        else:
            pinout = machine.Pin.OUT
            if a_in1 is not None:
                self._a_phase = machine.Pin(a_in1, pinout)
                self._a_phase.value(0)
                self._a_enable = machine.Pin(a_in2, pinout)
                self._a_pwm = machine.PWM(self._a_enable,
                                          freq=self.PWM_MAX_FREQ, duty=0)
            if b_in1 is not None:
                self._b_phase = machine.Pin(b_in1, pinout)
                self._b_phase.value(0)
                self._b_enable = machine.Pin(b_in2, pinout)
                self._b_pwm = machine.PWM(self._b_enable,
                                          freq=self.PWM_MAX_FREQ, duty=0)
            self.duty_a = self.phen_duty_a
            self.duty_b = self.phen_duty_b

    def inin_duty_a(self, duty):
        pass

    def inin_duty_b(self, duty):
        pass

    def phen_duty_a(self, duty):
        if duty >= 0.0:
            self._a_phase.value(0)
            self._a_pwm.duty(int(self.PWM_MAX_DUTY * duty))
        else:
            self._a_phase.value(1)
            self._a_pwm.duty(int(self.PWM_MAX_DUTY * -duty))

    def phen_duty_b(self, duty):
        if duty >= 0.0:
            self._b_phase.value(0)
            self._b_pwm.duty(int(self.PWM_MAX_DUTY * duty))
        else:
            self._b_phase.value(1)
            self._b_pwm.duty(int(self.PWM_MAX_DUTY * -duty))
            
    def phen_raw_a_duty(self, duty):
        self._a_pwm.duty(duty)
        
    def phen_raw_a_dir(self, value):
        self._a_phase.value(value)

    def phen_raw_b_duty(self, duty):
        self._b_pwm.duty(duty)
        
    def phen_raw_b_dir(self, value):
        self._b_phase.value(value)

