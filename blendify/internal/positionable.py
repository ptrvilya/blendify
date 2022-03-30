from abc import ABC, abstractmethod

import bpy
import numpy as np

from ..internal.types import BlenderGroup, Vector3d, Vector4d


class Positionable(ABC):
    """Base class for all classes that wrap Blender objects with location in space (Camera, Light, Renderable)
    """
    @abstractmethod
    def __init__(
            self,
            tag: str,
            blender_object: BlenderGroup,
            quaternion: Vector4d = (1, 0, 0, 0),
            translation: Vector3d = (0, 0, 0)
    ):
        """Sets initial position of the Blender object and stores it. Called from child classes

        Args:
            tag (str): name of the object in Blender that was created in child class
            blender_object (bpy.types.Object): instance of Blender Object that is wrapped by the child class
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
        """
        self._blender_object = blender_object
        self._tag = tag
        self.set_position(quaternion, translation)

    @property
    def tag(self):
        return self._tag

    def set_position(self, quaternion: Vector4d, translation: Vector3d):
        self._quaternion = np.array(quaternion, dtype=np.float64)
        self._translation = np.array(translation, dtype=np.float64)
        self._update_position()

    @property
    def quaternion(self):
        return self._quaternion

    @quaternion.setter
    def quaternion(self, val: Vector4d):
        self._quaternion = np.array(val)
        self._update_position()

    @property
    def translation(self):
        return self._translation

    @translation.setter
    def translation(self, val: Vector3d):
        self._translation = np.array(val)
        self._update_position()

    def _update_position(self):
        self._set_blender_object_position(self._blender_object)

    def _set_blender_object_position(self, blender_object: BlenderGroup):
        def set_position(obj):
            obj.rotation_mode = 'QUATERNION'
            obj.rotation_quaternion = self.quaternion.tolist()
            obj.location = self.translation.tolist()

        if isinstance(blender_object, bpy.types.Collection):
            for obj in blender_object.all_objects.values():
                set_position(obj)
        else:
            set_position(blender_object)

    def _blender_remove_object(self):
        """Removes the object from Blender scene"""
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        is_collection = isinstance(self._blender_object, bpy.types.Collection)
        if is_collection:
            for obj in self._blender_object.all_objects.values():
                obj.select_set(True)
        else:
            self._blender_object.select_set(True)
        bpy.ops.object.delete()
        if is_collection:
            bpy.data.collections.remove(self._blender_object)
        self._blender_object = None
