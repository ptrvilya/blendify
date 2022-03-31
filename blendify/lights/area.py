from abc import abstractmethod

import numpy as np

from .base import Light
from ..internal.types import Vector3d, Vector2d


class AreaLight(Light):
    """Base class for different AreaLights varying in shape.
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
        """Creates AreaLight light source in Blender. The method is called from child classes

        Args:
            color (Vector3d): color of the light source
            strength (float): strength of the light source emitted over the entire area of the light in all directions
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
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
        """Creates SquareAreaLight light source in Blender through constructor of the parent class AreaLight

        Args:
            size (float): size of the area of the area light
            strength (float): strength of the light source
            color (Vector3d): color of the light source
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
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
        """Creates CircleAreaLight light source in Blender through constructor of the parent class AreaLight

        Args:
            size (float): size of the area of the area light
            strength (float): strength of the light source emitted over the entire area of the light in all directions
            color (Vector3d): color of the light source
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
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
        """Creates RectangleAreaLight light source in Blender through constructor of the parent class AreaLight

        Args:
            size (Vector2d): [x, y] sizes of the area light
            strength (float): strength of the light source emitted over the entire area of the light in all directions
            color (Vector3d): color of the light source
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
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
        """Creates EllipseAreaLight light source in Blender through constructor of the parent class AreaLight

        Args:
            size (Vector2d): [x, y] sizes of the area light
            strength (float): strength of the light source emitted over the entire area of the light in all directions
            color (Vector3d): color of the light source
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
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
