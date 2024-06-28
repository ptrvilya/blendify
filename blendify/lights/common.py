from .base import Light
from ..internal.types import Vector3d


class PointLight(Light):
    def __init__(
        self,
        strength: float,
        shadow_soft_size: float,
        color: Vector3d,
        tag: str,
        cast_shadows: bool = True,
        **kwargs
    ):
        """Creates PointLight light source in Blender

        Args:
            strength (float): strength of the light source emitted over the entire area of the light in all directions
            shadow_soft_size (float): light size for ray shadow sampling (Raytraced shadows) in [0, inf]
            color (Vector3d): color of the light source
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
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
        blender_light = self._blender_create_light(tag, "POINT")
        super().__init__(**kwargs, tag=tag, blender_object=blender_light)
        self.color = color
        self.strength = strength
        self.cast_shadows = cast_shadows
        self.shadow_soft_size = shadow_soft_size

    @property
    def shadow_soft_size(self) -> float:
        return self.blender_light.data.shadow_soft_size

    @shadow_soft_size.setter
    def shadow_soft_size(self, val: float):
        self.blender_light.data.shadow_soft_size = val


class DirectionalLight(Light):
    def __init__(
        self,
        strength: float,
        angular_diameter: float,
        color: Vector3d,
        tag: str,
        cast_shadows: bool = True,
        **kwargs
    ):
        """Creates DirectionalLight light source in Blender

        Args:
            strength (float): strength of the light source in watts per meter squared (W/m^2)
            angular_diameter (float): angular diameter of the Sun as seen from the Earth in [0, 3.14159]
            color (Vector3d): color of the light source
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
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
        blender_light = self._blender_create_light(tag, "SUN")
        super().__init__(**kwargs, tag=tag, blender_object=blender_light)
        self.color = color
        self.strength = strength
        self.cast_shadows = cast_shadows
        self.angular_diameter = angular_diameter

    @property
    def angular_diameter(self) -> float:
        return self.blender_light.data.angle

    @angular_diameter.setter
    def angular_diameter(self, val: float):
        self.blender_light.data.angle = val


class SpotLight(Light):
    def __init__(
        self,
        strength: float,
        spot_size: float,
        spot_blend: float,
        color: Vector3d,
        shadow_soft_size: float,
        tag: str,
        cast_shadows: bool = True,
        **kwargs
    ):
        """Creates SpotLight light source in Blender

        Args:
            strength (float): strength of the light source that light would emit over its entire area if
                it wasn't limited by the spot angle
            spot_size (float): angle of the spotlight beam in [0.0174533, 3.14159]
            spot_blend (float): the softness of the spotlight edge in [0, 1]
            color (Vector3d): color of the light source
            shadow_soft_size (float): light size for ray shadow sampling (Raytraced shadows) in [0, inf]
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
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
        # spot_size: Angle of the spotlight beam (float in [0.0174533, 3.14159]) default 0.785398
        # spot_blend: The softness of the spotlight edge (float in [0, 1]) default 0.15
        blender_light = self._blender_create_light(tag, "SPOT")
        super().__init__(**kwargs, tag=tag, blender_object=blender_light)
        self.color = color
        self.strength = strength
        self.spot_size = spot_size
        self.spot_blend = spot_blend
        self.cast_shadows = cast_shadows
        self.shadow_soft_size = shadow_soft_size

    @property
    def spot_size(self) -> float:
        return self.blender_light.data.spot_size

    @spot_size.setter
    def spot_size(self, val: float):
        self.blender_light.data.spot_size = val

    @property
    def spot_blend(self) -> float:
        return self.blender_light.data.spot_blend

    @spot_blend.setter
    def spot_blend(self, val: float):
        self.blender_light.data.spot_blend = val

    @property
    def shadow_soft_size(self) -> float:
        return self.blender_light.data.shadow_soft_size

    @shadow_soft_size.setter
    def shadow_soft_size(self, val: float):
        self.blender_light.data.shadow_soft_size = val
