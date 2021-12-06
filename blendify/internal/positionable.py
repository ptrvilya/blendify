import numpy as np
from typing import Union, Tuple, List, Sequence
from abc import ABC, abstractmethod


class Positionable(ABC):
    @abstractmethod
    def __init__(self):
        self._quaternion = np.array([1, 0, 0, 0], dtype=np.float64)
        self._translation = np.zeros(3, dtype=np.float64)

    def set_position(self, quaternion: np.ndarray, translation: np.ndarray):
        self._quaternion = quaternion
        self._translation = translation

    @property
    def quaternion(self):
        return self._quaternion

    @quaternion.setter
    def quaternion(self, quat):
        self._quaternion = quat

    @property
    def translation(self):
        return self._translation

    @translation.setter
    def translation(self, tr):
        self._translation = tr
