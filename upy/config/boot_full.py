from configobj import Config

config = Config()
config.services = ['admin', 'airterm']
config.ssd1331 = True
config.progress_ssd1331 = True
config.enable_wifi_pin = 36		# PIN Number or None
