from ..internal import Singleton


class RenderablesCollection(metaclass=Singleton):
    _renderables = {}

    def __init__(self):
        pass

    @classmethod
    def __getitem__(cls, key):
        return cls._renderables[key]
