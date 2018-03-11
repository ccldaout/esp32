from configobj import Config

config = Config()
config.port = 2002
config.drv8835_mode = 1			# 1:PH_EN, 0:IN_IN
config.A_in1 = 14
config.A_in2 = 12
config.B_in1 = 33
config.B_in2 = 25
config.qtr3rc_pins = (26, 27, 15)
