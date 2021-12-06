import numpy as np
from typing import Union, Tuple, List, Sequence
from abc import ABC, abstractmethod
from blendify.cameras import Camera
from .visuals import Visuals


class Renderable(ABC):
    def __init__(self, camera: Camera):
        self._camera = camera
        self._visuals = None

    def _set_camera(self, camera: Camera):
        pass

    def set_camera(self, camera: Camera):
        self._set_camera(camera)
        self._camera = camera

    @property
    def visuals(self):
        return self._visuals

    @visuals.setter
    def visuals(self, visual:Visuals):
        self._visuals = visual