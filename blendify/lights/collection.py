from typing import Dict, Iterable

from ..internal import Singleton
from ..lights import Light


class LightsCollection(metaclass=Singleton):
    _lights: Dict[str, Light] = dict()

    def __init__(self):
        pass

    @classmethod
    def add_sun(cls):
        pass

    @classmethod
    def add_point(cls):
        pass

    @classmethod
    def add_spot(cls):
        pass

    @classmethod
    def add_area(cls):
        pass

    @classmethod
    def __getitem__(cls, key: str) -> Light:
        return cls._lights[key]

    @classmethod
    def __setitem__(cls, key: str, value: Light):
        cls._lights[key] = value

    @classmethod
    def __delitem__(cls, key: str):
        del cls.__dict__[key]

    @classmethod
    def __iter__(cls) -> Iterable:
        return iter(cls._lights)

    @classmethod
    def __len__(cls) -> int:
        return len(cls._lights)

    # def __str__(self):
    #     return str(self.__dict__)
    #
    # def __repr__(self):
    #     return '{}, D({})'.format(super(D, self).__repr__(), self.__dict__)
