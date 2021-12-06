import numpy as np
from typing import Union, Tuple, List, Sequence
from abc import ABC, abstractmethod

class Positionable(ABC):
    @abstractmethod
    def __init__(self):
        self._quaternion = np.array([1,0,0,0], dtype=np.float64)
        self._translation = np.zeros(3, dtype=np.float64)