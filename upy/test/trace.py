import time
import drv8835
from sensor import QTRxRC
from config.service_robot1 import config

DUTY_ST  = 300
DUTY_MIN = 200		# duty lower: 200
ROT1_MS  = 5300
ROT1_DURATION = 10

class Motor(object):
    def __init__(self):
        self._drv = drv8835.DRV8835(config.drv8835_mode,
                                    config.A_in1, config.A_in2,
                                    config.B_in1, config.B_in2)
        self._a_duty = 0
        self._b_duty = 0

    def start(self):
        self._drv.phen_raw_a_dir(0)
        self._drv.phen_raw_b_dir(0)

    def duty(self, a_duty, b_duty):
        self._a_duty = a_duty
        self._b_duty = b_duty
        self._drv.phen_raw_a_duty(self._a_duty)
        self._drv.phen_raw_b_duty(self._b_duty)

    def straight(self):
        self.duty(DUTY_ST, DUTY_ST)

    def turn_L(self, r_plus):
        self.duty(DUTY_MIN, DUTY_MIN+r_plus)

    def turn_R(self, l_plus):
        self.duty(DUTY_MIN+l_plus, DUTY_MIN)

    def stop(self):
        self._drv.phen_raw_a_duty(0)
        self._drv.phen_raw_b_duty(0)
        self._drv.phen_raw_a_dir(0)
        self._drv.phen_raw_b_dir(0)

    def _rotate(self, a_dir, b_dir, duration_ms):
        self.stop()
        self._drv.phen_raw_a_dir(a_dir)
        self._drv.phen_raw_b_dir(b_dir)
        self.duty(DUTY_MIN, DUTY_MIN)
        time.sleep_ms(duration_ms)
        self.stop()

    def rotate_L(self, duration_ms):
        self._rotate(0, 1, duration_ms)		# 1cycle/5.3sec

    def rotate_R(self, duration_ms):
        self._rotate(1, 0, duration_ms)

INIT = 0
GSEARCH = 1
SHIFT_R = 2
SHIFT_R2 = 3
ROTATE_R = 4
ONLINE_FROM_R = 5
ONLINE_CONT = 6
ONLINE_FROM_L = 7
ROTATE_L = 8
SHIFT_L2 = 9
SHIFT_L = 10

FSM = {
    #               00        01        10        11
    INIT:          (GSEARCH,  SHIFT_R,  SHIFT_L,  ONLINE_CONT),
    GSEARCH:       (GSEARCH,  ROTATE_R, ROTATE_L, ONLINE_CONT),
    #
    SHIFT_R:       (SHIFT_R2, SHIFT_R,  SHIFT_L,  ONLINE_FROM_L),
    SHIFT_R2:      (ROTATE_R, SHIFT_R,  SHIFT_L,  ONLINE_FROM_L),
    ROTATE_R:      (GSEARCH,  SHIFT_R,  SHIFT_L,  ONLINE_FROM_L),
    ONLINE_FROM_L: (SHIFT_L,  SHIFT_R,  SHIFT_L,  ONLINE_CONT),
    ONLINE_CONT:   (SHIFT_R,  SHIFT_R,  SHIFT_L,  ONLINE_CONT),
    ONLINE_FROM_R: (SHIFT_R,  SHIFT_R,  SHIFT_L,  ONLINE_CONT),
    ROTATE_L:      (GSEARCH,  SHIFT_R,  SHIFT_L,  ONLINE_FROM_R),
    SHIFT_L2:      (ROTATE_L, SHIFT_R,  SHIFT_L,  ONLINE_FROM_R),
    SHIFT_L:       (SHIFT_L2, SHIFT_R,  SHIFT_L,  ONLINE_FROM_R),
}

class Car(object):

    def __init__(self):
        self.act = {
            INIT:          None,
            GSEARCH:       self.search,
            SHIFT_R:       self.shift_r,
            SHIFT_R2:      self.shift_r2,
            ROTATE_R:      self.rotate_r,
            ONLINE_FROM_L: self.online_from_l,
            ONLINE_CONT:   self.online_cont,
            ONLINE_FROM_R: self.online_from_r,
            ROTATE_L:      self.rotate_l,
            SHIFT_L2:      self.shift_l2,
            SHIFT_L:       self.shift_l,
        }

        self._motor = Motor()
        self._qtr = QTRxRC()
        self._qtr.add_sensor(27, 20, 40, 35)	# mid -> right
        self._qtr.add_sensor(26, 20, 40, 35)	# left

    def sens(self):
        v = 0
        for bit_pos, bval in enumerate(self._qtr.sense_black()):
            v |= (int(bval) << bit_pos)
        # left<<1, mid(right)<<0
        return v

    def trace(self):
        sens_str = {0b00:'__', 0b01:'_B', 0b10:'B_', 0b11:'BB'}
        state_str = {INIT:'INIT', GSEARCH:'GSEARCH', SHIFT_R:'SHIFT_R', SHIFT_R2:'SHIFT_R2',
                     ROTATE_R:'ROTATE_R', ONLINE_FROM_L:'ONLINE_FROM_L', ONLINE_CONT:'ONLINE_CONT',
                     ONLINE_FROM_R:'ONLINE_FROM_R', ROTATE_L:'ROTATE_L', SHIFT_L2:'SHIFT_L2',
                     SHIFT_L:'SHIFT_L'}
        self._motor.start()
        cur_state = INIT
        while True:
            sens = self.sens()
            new_state = FSM[cur_state][sens]
            print(state_str[cur_state], sens_str[sens], '->', state_str[new_state])
            action = self.act.get(new_state)
            if action:
                action()
            cur_state = new_state
            time.sleep_ms(20)
            self._motor.stop()

    def search(self):
        self._motor.turn_L(100)

    def shift_r(self):
        self._motor.turn_R(30)

    def shift_r2(self):
        self._motor.turn_R(50)

    def rotate_r(self):
        for _ in range(ROT1_MS//ROT1_DURATION):
            self._motor.rotate_R(ROT1_DURATION)
            sens = self.sens()
            if sens == 0b11:
                return
        for _ in range(ROT1_MS//ROT1_DURATION):
            self._motor.rotate_R(ROT1_DURATION)
            sens = self.sens()
            if sens == 0b01 or sens == 0b10:
                return

    def online_from_l(self):
        self._motor.turn_L(1)

    def online_cont(self):
        self._motor.straight()

    def online_from_r(self):
        self._motor.turn_R(1)

    def rotate_l(self):
        for _ in range(ROT1_MS//ROT1_DURATION):
            self._motor.rotate_L(ROT1_DURATION)
            sens = self.sens()
            if sens == 0b11:
                return
        for _ in range(ROT1_MS//ROT1_DURATION):
            self._motor.rotate_L(ROT1_DURATION)
            sens = self.sens()
            if sens == 0b01 or sens == 0b10:
                return

    def shift_l2(self):
        self._motor.turn_L(50)

    def shift_l(self):
        self._motor.turn_L(30)

car = Car()
motor = car._motor
car.trace()
