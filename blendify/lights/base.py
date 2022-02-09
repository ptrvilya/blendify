from abc import abstractmethod

import bpy
import numpy as np

from ..internal.positionable import Positionable
from ..internal.types import Vector2d, Vector3d, Vector4d


class Light(Positionable):
    """
    Abstract base class for all the light sources.
    """
    @abstractmethod
    def __init__(
        self,
        **kwargs
    ):
        """
        Passes all arguments to the constructor of the base class.
        Args:
            blender_object (bpy.types.Object): instance of Blender Object that is wrapped by the class
            quaternion (Vector4d, optional): rotation to apply to Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation to apply to the Blender object (default: (0,0,0))
            tag (str): name of the object in Blender that is created
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
        """
        Creates PointLight light source in Blender.
        Args:
            strength (float): strength of the light source emitted over the entire area of the light in all directions
            shadow_soft_size (float): light size for ray shadow sampling (Raytraced shadows) in [0, inf]
            color (Vector3d): color of the light source
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation to apply to Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation to apply to the Blender object (default: (0,0,0))
            tag (str): name of the object in Blender that is created
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
        """
        Creates DirectionalLight light source in Blender.
        Args:
            strength (float): strength of the light source in watts per meter squared (W/m^2)
            angular_diameter (float): angular diameter of the Sun as seen from the Earth in [0, 3.14159]
            color (Vector3d): color of the light source
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation to apply to Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation to apply to the Blender object (default: (0,0,0))
            tag (str): name of the object in Blender that is created
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
        """
        Creates SpotLight light source in Blender.
        Args:
            strength (float): strength of the light source that light would emit over its entire area if
                it wasn't limited by the spot angle
            spot_size (float): angle of the spotlight beam in [0.0174533, 3.14159]
            spot_blend (float): the softness of the spotlight edge in [0, 1]
            color (Vector3d): color of the light source
            shadow_soft_size (float): light size for ray shadow sampling (Raytraced shadows) in [0, inf]
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation to apply to Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation to apply to the Blender object (default: (0,0,0))
            tag (str): name of the object in Blender that is created
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


class AreaLight(Light):
    """
    Base class for different AreaLights varying in shape.
    """
    @abstractmethod
    def __init__(
        self,
        color: Vector3d,
        strength: float,
        tag: str,
        cast_shadows: bool = True,
        **kwargs
    ):
        """
        Creates AreaLight light source in Blender. The method is called from child classes.
        Args:
            color (Vector3d): color of the light source
            strength (float): strength of the light source emitted over the entire area of the light in all directions
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation to apply to Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation to apply to the Blender object (default: (0,0,0))
            tag (str): name of the object in Blender that is created
        """
        blender_light = self._blender_create_light(tag, "AREA")
        super().__init__(**kwargs, tag=tag, blender_object=blender_light)
        self.color = color
        self.strength = strength
        self.cast_shadows = cast_shadows


class SquareAreaLight(AreaLight):
    def __init__(
        self,
        size: float,
        **kwargs
    ):
        """
        Creates SquareAreaLight light source in Blender through constructor of the parent class AreaLight.
        Args:
            size (float): size of the area of the area light
            strength (float): strength of the light source
            color (Vector3d): color of the light source
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation to apply to Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation to apply to the Blender object (default: (0,0,0))
            tag (str): name of the object in Blender that is created
        """
        super().__init__(**kwargs)
        self.blender_light.data.shape = "SQUARE"
        self.size = size

    @property
    def size(self) -> float:
        return self.blender_light.data.size

    @size.setter
    def size(self, val: float):
        self.blender_light.data.size = val


class CircleAreaLight(AreaLight):
    def __init__(
        self,
        size: float,
        **kwargs
    ):
        """
        Creates CircleAreaLight light source in Blender through constructor of the parent class AreaLight.
        Args:
            size (float): size of the area of the area light
            strength (float): strength of the light source emitted over the entire area of the light in all directions
            color (Vector3d): color of the light source
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation to apply to Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation to apply to the Blender object (default: (0,0,0))
            tag (str): name of the object in Blender that is created
        """
        super().__init__(**kwargs)
        self.blender_light.data.shape = "DISK"
        self.size = size

    @property
    def size(self) -> float:
        return self.blender_light.data.size

    @size.setter
    def size(self, val: float):
        self.blender_light.data.size = val


class RectangleAreaLight(AreaLight):
    def __init__(
        self,
        size: Vector2d,
        **kwargs
    ):
        """
        Creates RectangleAreaLight light source in Blender through constructor of the parent class AreaLight.
        Args:
            size (Vector2d): [x, y] sizes of the area light
            strength (float): strength of the light source emitted over the entire area of the light in all directions
            color (Vector3d): color of the light source
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation to apply to Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation to apply to the Blender object (default: (0,0,0))
            tag (str): name of the object in Blender that is created
        """
        super().__init__(**kwargs)
        self.blender_light.data.shape = "RECTANGLE"
        self.size = size

    @property
    def size(self) -> np.ndarray:
        return np.array([self.blender_light.data.size, self.blender_light.data.size_y])

    @size.setter
    def size(self, val: Vector2d):
        self.blender_light.data.size = val[0]
        self.blender_light.data.size_y = val[1]


class EllipseAreaLight(AreaLight):
    def __init__(
        self,
        size: Vector2d,
        **kwargs
    ):
        """
        Creates EllipseAreaLight light source in Blender through constructor of the parent class AreaLight.
        Args:
            size (Vector2d): [x, y] sizes of the area light
            strength (float): strength of the light source emitted over the entire area of the light in all directions
            color (Vector3d): color of the light source
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation to apply to Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation to apply to the Blender object (default: (0,0,0))
            tag (str): name of the object in Blender that is created
        """
        super().__init__(**kwargs)
        self.blender_light.data.shape = "ELLIPSE"
        self.size = size

    @property
    def size(self) -> np.ndarray:
        return np.array([self.blender_light.data.size, self.blender_light.data.size_y])

    @size.setter
    def size(self, val: Vector2d):
        self.blender_light.data.size = val[0]
        self.blender_light.data.size_y = val[1]
