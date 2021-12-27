import numpy as np
import bpy
from ..internal.types import BlenderGroup
from typing import Union, Tuple, List, Sequence
from abc import ABC, abstractmethod


class Positionable(ABC):
    @abstractmethod
    def __init__(self, tag: str, blender_object: BlenderGroup):
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

    def _set_blender_object_position(self, blender_object: BlenderGroup):
        def set_position(obj):
            obj.rotation_mode = 'QUATERNION'
            obj.rotation_quaternion = self.quaternion.tolist()
            obj.position = self.translation.tolist()
        if isinstance(blender_object, bpy.types.Collection):
            for obj in blender_object.all_objects.values():
                set_position(obj)
        else:
            set_position(blender_object)

    def _blender_remove_object(self):
        """Removes the object from Blender scene"""
        bpy.ops.object.select_all(action='DESELECT')
        if isinstance(self._blender_object, bpy.types.Collection):
            for obj in self._blender_object.all_objects.values():
                obj.select_set(True)
        else:
            self._blender_object.select_set(True)
        bpy.ops.object.delete()
        if isinstance(self._blender_object, bpy.types.Collection):
            bpy.data.collections.remove(self._blender_object)
        self._blender_object = None
