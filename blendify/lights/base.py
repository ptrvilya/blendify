from abc import abstractmethod

import bpy
import numpy as np

from ..internal.positionable import Positionable
from ..internal.types import Vector3d


class Light(Positionable):
    """Abstract base class for all the light sources.
    """
    @abstractmethod
    def __init__(
        self,
        **kwargs
    ):
        """Passes all arguments to the constructor of the base class

        Args:
            blender_object (bpy.types.Object): instance of Blender Object that is wrapped by the class
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        super().__init__(**kwargs)

    def _blender_create_light(self, tag: str, light_type: str) -> bpy.types.Object:
        light_obj = bpy.data.lights.new(name=tag, type=light_type)
        obj = bpy.data.objects.new(name=tag, object_data=light_obj)

        bpy.context.collection.objects.link(obj)
        return obj

    @property
    def blender_light(self) -> bpy.types.Object:
        return self._blender_object

    @property
    def color(self) -> np.ndarray:
        return np.array(self.blender_light.data.color[:3])

    @color.setter
    def color(self, val: Vector3d):
        val = np.array(val)
        self.blender_light.data.color = val.tolist()

    @property
    def cast_shadows(self) -> bool:
        return self.blender_light.data.cycles.cast_shadow

    @cast_shadows.setter
    def cast_shadows(self, val: bool):
        self.blender_light.data.cycles.cast_shadow = val

    @property
    def strength(self) -> float:
        return self.blender_light.data.energy

    @strength.setter
    def strength(self, val: float):
        self.blender_light.data.energy = val

    @property
    def max_bounces(self) -> int:
        return self.blender_light.data.cycles.max_bounces

    @max_bounces.setter
    def max_bounces(self, val: int):
        self.blender_light.data.cycles.max_bounces = val
