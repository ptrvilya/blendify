import numpy as np
import bpy_types
from typing import Union, Tuple, List, Sequence
from abc import ABC, abstractmethod


class Positionable(ABC):
    @abstractmethod
    def __init__(self, tag: str, blender_object: bpy_types.Object):
        self._quaternion = np.array([1, 0, 0, 0], dtype=np.float64)
        self._translation = np.zeros(3, dtype=np.float64)
        self._blender_object = blender_object
        self._tag = tag
        self._update_blender_position()

    @property
    def tag(self):
        return self._tag

    def set_position(self, quaternion: np.ndarray, translation: np.ndarray):
        self._quaternion = np.array(quaternion)
        self._translation = np.array(translation)
        self._update_blender_position()

    @property
    def quaternion(self):
        return self._quaternion

    @quaternion.setter
    def quaternion(self, quat: Sequence[float]):
        self._quaternion = np.array(quat)
        self._update_blender_position()

    @property
    def translation(self):
        return self._translation

    @translation.setter
    def translation(self, tr: Sequence[float]):
        self._translation = np.array(tr)
        self._update_blender_position()

    def _update_blender_position(self):
        self._set_blender_object_position(self._blender_object)

    def _set_blender_object_position(self, blender_object: bpy_types.Object):
        blender_object.rotation_mode = 'QUATERNION'
        blender_object.rotation_quaternion = self.quaternion.tolist()
        blender_object.position = self.translation.tolist()
