from ..internal import Singleton


class LightsCollection(metaclass=Singleton):
    _lights = {}

    def __init__(self):
        pass

    @classmethod
    def __getitem__(cls, key):
        return cls._lights[key]
