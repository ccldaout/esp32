from configobj import Config

# my own SSD1331
config = Config()
config.split_COM_odd_even = True	# BUG on chip
config.color_format = 1		# 0:256, 1:65k1, 2:65k2
config.pin_dc = 16
config.pin_rst = 4
