from typing import Dict, Iterable

from ..internal import Singleton
from ..lights import Light


class LightsCollection(metaclass=Singleton):
    def __init__(self):
        self._lights: Dict[str, Light] = dict()

    def add_sun(self):
        pass

    def add_point(self):
        pass

    def add_spot(self):
        pass

    def add_area(self):
        pass

    def __getitem__(self, key: str) -> Light:
        return self._lights[key]

    def __setitem__(self, key: str, value: Light):
        self._lights[key] = value

    def __delitem__(self, key: str):
        del self.__dict__[key]

    def __iter__(self) -> Iterable:
        return iter(self._lights)

    def __len__(self) -> int:
        return len(self._lights)

    # def __str__(self):
    #     return str(self.__dict__)
    #
    # def __repr__(self):
    #     return '{}, D({})'.format(super(D, self).__repr__(), self.__dict__)
