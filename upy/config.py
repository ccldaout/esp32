class Config(object):
    def __getattr__(self, name):
        return None

    def get(self, name, default=None):
        if name not in self.__dict__:
            return default
        return getattr(self, name)

ssd1331 = Config()

# my own SSD1331
ssd1331.split_COM_odd_even = True	# BUG on chip
ssd1331.color_format = 1		# 0:256, 1:65k1, 2:65k2
