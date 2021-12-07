import numpy as np
import bpy_types
from typing import Union, Tuple, List, Sequence
from abc import ABC, abstractmethod
from ..cameras import Camera
from .visuals import Visuals
from ..internal.positionable import Positionable


class Renderable(Positionable):
    def __init__(self, visuals: Visuals, tag: str, blender_object: bpy_types.Object):
        super().__init__(tag, blender_object)
        self._current_visuals_type = None
        self.update_visuals(visuals)

    def update_camera(self, camera: Camera):
        pass

    @abstractmethod
    def _blender_clear_visuals(self):
        pass

    @abstractmethod
    def _blender_set_visuals(self, visuals: Visuals):
        pass

    def update_visuals(self, visuals: Visuals):
        if self._current_visuals_type is not None:
            self._blender_clear_visuals()
        self._current_visuals_type = visuals.__class__.__name__
        self._blender_set_visuals(visuals)
