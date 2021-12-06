import numpy as np
from typing import Union, Tuple, List, Sequence
from abc import ABC, abstractmethod
from blendify.cameras import Camera
from .visuals import Visuals
from ..internal.positionable import Positionable


class Renderable(Positionable):
    def __init__(self, tag:str):
        self._tag = tag

    def update_camera(self, camera: Camera):
        pass

    @property
    def tag(self):
        return self._tag

    @abstractmethod
    def update_visuals(self, visuals: Visuals):
        pass
