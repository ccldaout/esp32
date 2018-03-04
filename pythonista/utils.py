# coding: utf-8

import cPickle

class Config(object):
	@staticmethod
	def load(path):
		try:
			with open(path) as f:
				config = cPickle.load(f)
		except:
			config = Config()
		config._path = path
		return config

	def __getattr__(self, name):
		if name[:2] == '__':
			raise AttributeError()
		return None

	def get(self, name, default=None):
		if hasattr(self, name):
			return getattr(self, name)
		return default
		
	def save(self):
		try:
			with open(self._path, 'wb') as f:
				cPickle.dump(self, f, cPickle.HIGHEST_PROTOCOL)
		except:
			raise
