class Config(object):
    def __getattr__(self, name):
        return None

    def get(self, name, default=None):
        if name not in self.__dict__:
            return default
        return getattr(self, name)

# my own SSD1331
ssd1331 = Config()
ssd1331.split_COM_odd_even = True	# BUG on chip
ssd1331.color_format = 1		# 0:256, 1:65k1, 2:65k2
ssd1331.pin_dc = 16
ssd1331.pin_rst = 4

# ROBOT
robot = Config()
robot.drv8835_mode = 1			# 1:PH_EN, 0:IN_IN
robot.A_in1 = 14
robot.A_in2 = 12
robot.B_in1 = 33
robot.B_in2 = 25

#  HCSR04
hcsr04 = Config()
hcsr04.pin_echo = 35
hcsr04.pin_trig = 32
