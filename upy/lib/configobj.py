class Config(object):
    def __getattr__(self, name):
        return None

    def get(self, name, default=None):
        if name not in self.__dict__:
            return default
        return getattr(self, name)

empty_config = Config()
