from abc import abstractmethod

import bpy
import numpy as np

from ..internal.positionable import Positionable
from ..internal.types import Vector3d, RotationParams


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
            rotation_mode (str): type of rotation representation.
                Can be one of the following:
                - "quaternionWXYZ" - WXYZ quaternion
                - "quaternionXYZW" - XYZW quaternion
                - "rotvec" - axis-angle representation of rotation
                - "rotmat" - 3x3 rotation matrix
                - "euler<mode>" - Euler angles with the specified order of rotation, e.g. XYZ, xyz, ZXZ, etc. Refer to scipy.spatial.transform.Rotation.from_euler for details.
                - "look_at" - look at rotation, the rotation is defined by the point to look at and, optional, the rotation around the forward direction vector (a single float value in tuple or list)
            rotation (RotationParams): rotation parameters according to the rotation_mode
                - for "quaternionWXYZ" and "quaternionXYZW" - Vec4d
                - for "rotvec" - Vec3d
                - for "rotmat" - Mat3x3
                - for "euler<mode>" - Vec3d
                - for "look_at" - Vec3d, Positionable or Tuple[Vec3d/Positionable, float], where float is the rotation around the forward direction vector in degrees
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
