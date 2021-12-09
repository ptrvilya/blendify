import numpy as np
import bpy
import bpy_types
from abc import ABC, abstractmethod
from typing import Union, Tuple, List, Sequence
from ..internal.positionable import Positionable
from ..internal.types import Vector2d, Vector3d


class Light(Positionable):
    @abstractmethod
    def __init__(self, tag: str, light_object:bpy_types.Object):
        super().__init__(tag, light_object)

    def _blender_create_light(self, tag: str, light_type:str) -> bpy_types.Object:
        return bpy.data.lights.new(name=tag, type=light_type)

    @property
    def blender_light(self) -> bpy_types.Object:
        return self._blender_object

    @property
    def color(self) -> np.ndarray:
        return np.array(self.blender_light.data.color[:3])

    @color.setter
    def color(self, val:Vector3d):
        val = np.array(val)
        self.blender_light.data.color = val.tolist() + [1.]

    @property
    def cast_shadows(self) -> bool:
        return self.blender_light.data.cycles.cast_shadow

    @cast_shadows.setter
    def cast_shadows(self, val:bool):
        self.blender_light.data.cycles.cast_shadow = val

    @property
    def strength(self) -> float:
        return self.blender_light.data.energy

    @strength.setter
    def strength(self, val:float):
        self.blender_light.data.energy = val

    @property
    def max_bounces(self) -> int:
        return self.blender_light.data.cycles.max_bounces

    @max_bounces.setter
    def max_bounces(self, val: int):
        self.blender_light.data.cycles.max_bounces = val


class PointLight(Light):
    def __init__(self, color:Vector3d, strength: float,
            shadow_soft_size:float, tag:str, cast_shadows:bool = True):
        blender_light = self._blender_create_light(tag, "POINT")
        super().__init__(tag, blender_light)
        self.color = color
        self.strength = strength
        self.cast_shadows = cast_shadows
        self.shadow_soft_size = shadow_soft_size

    @property
    def shadow_soft_size(self) -> float:
        return self.blender_light.data.shadow_soft_size

    @shadow_soft_size.setter
    def shadow_soft_size(self, val:float):
        self.blender_light.data.shadow_soft_size = val


class DirectionalLight(Light):
    def __init__(self, color:Vector3d, strength: float,
            angular_diameter:float, tag:str, cast_shadows:bool = True):
        blender_light = self._blender_create_light(tag, "SUN")
        super().__init__(tag, blender_light)
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
    def __init__(self, color: Vector3d, strength: float,
            shadow_soft_size: float, tag: str, cast_shadows: bool = True):
        blender_light = self._blender_create_light(tag, "SPOT")
        super().__init__(tag, blender_light)
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


class AreaLight(Light):
    @abstractmethod
    def __init__(self, color: Vector3d, strength: float,
            tag: str, cast_shadows: bool = True):
        blender_light = self._blender_create_light(tag, "AREA")
        super().__init__(tag, blender_light)
        self.color = color
        self.strength = strength
        self.cast_shadows = cast_shadows


class SquareAreaLight(AreaLight):
    def __init__(self, size:float, color: Vector3d, strength: float,
            tag: str, cast_shadows: bool = True):
        super().__init__(color, strength, tag, cast_shadows)
        self.blender_light.data.shape = "SQUARE"
        self.size = size

    @property
    def size(self) -> float:
        return self.blender_light.data.size

    @size.setter
    def size(self, val: float):
        self.blender_light.data.size = val


class CircleAreaLight(AreaLight):
    def __init__(self, size:float, color: Vector3d, strength: float,
            tag: str, cast_shadows: bool = True):
        super().__init__(color, strength, tag, cast_shadows)
        self.blender_light.data.shape = "DISK"
        self.size = size

    @property
    def size(self) -> float:
        return self.blender_light.data.size

    @size.setter
    def size(self, val: float):
        self.blender_light.data.size = val


class RectangleAreaLight(AreaLight):
    def __init__(self, size:Vector2d, color: Vector3d, strength: float,
            tag: str, cast_shadows: bool = True):
        super().__init__(color, strength, tag, cast_shadows)
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
    def __init__(self, size:Vector2d, color: Vector3d, strength: float,
            tag: str, cast_shadows: bool = True):
        super().__init__(color, strength, tag, cast_shadows)
        self.blender_light.data.shape = "ELLIPSE"
        self.size = size

    @property
    def size(self) -> np.ndarray:
        return np.array([self.blender_light.data.size, self.blender_light.data.size_y])

    @size.setter
    def size(self, val: Vector2d):
        self.blender_light.data.size = val[0]
        self.blender_light.data.size_y = val[1]
