from typing import Dict, Iterable, Union

from .base import Light
from .common import PointLight, DirectionalLight, SpotLight
from .area import AreaLight, SquareAreaLight, CircleAreaLight, RectangleAreaLight, EllipseAreaLight
from ..internal import Singleton
from ..internal.types import Vector2d, Vector3d, Vector4d


class LightsCollection(metaclass=Singleton):
    def __init__(self):
        self._lights: Dict[str, Light] = dict()

    def add_point(
        self,
        strength: float = 100,
        shadow_soft_size: float = 0.25,
        color: Vector3d = (1.0, 1.0, 1.0),
        cast_shadows=True,
        quaternion: Vector4d = (1, 0, 0, 0),
        translation: Vector3d = (0, 0, 0),
        tag=None
    ) -> PointLight:
        """Add PointLight light source to the scene

        Args:
            strength (float, optional): strength of the light source emitted over the entire area of the light
                in all directions (default: 100)
            shadow_soft_size (float, optional): light size for ray shadow sampling (Raytraced shadows)
                in [0, inf] (default: 0.25)
            color (Vector3d, optional): color of the light source (default: (1.0, 1.0, 1.0))
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str, optional): name of the created collection in Blender to represent the point cloud.
                If None is passed the tag is automatically generated (default: None)

        Returns:
            PointLight: created and added to the scene object
        """
        tag = self._process_tag(tag, "Point")
        light = PointLight(
            color=color, strength=strength, shadow_soft_size=shadow_soft_size, cast_shadows=cast_shadows,
            quaternion=quaternion, translation=translation, tag=tag
        )
        self._lights[tag] = light
        return light

    def add_sun(
        self,
        strength: float = 10,
        angular_diameter: float = 0.00918043,
        color: Vector3d = (1.0, 1.0, 1.0),
        cast_shadows=True,
        quaternion: Vector4d = (1, 0, 0, 0),
        translation: Vector3d = (0, 0, 0),
        tag=None
    ) -> DirectionalLight:
        """Add DirectionalLight light source to the scene

        Args:
            strength (float, optional): strength of the light source in watts per meter squared (W/m^2) (default: 100)
            angular_diameter (float, optional): angular diameter of the Sun as seen from the Earth
                in [0, 3.14159] (default: 0.00918043)
            color (Vector3d, optional): color of the light source (default: (1.0, 1.0, 1.0))
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str, optional): name of the created collection in Blender to represent the point cloud.
                If None is passed the tag is automatically generated (default: None)

        Returns:
            DirectionalLight: created and added to the scene object
        """
        # angular_diameter: Angular diameter of the Sun as seen from the Earth,  [0, 3.14159]
        tag = self._process_tag(tag, "Sun")
        light = DirectionalLight(
            color=color, strength=strength, angular_diameter=angular_diameter, cast_shadows=cast_shadows,
            quaternion=quaternion, translation=translation, tag=tag
        )
        self._lights[tag] = light
        return light

    def add_spot(
        self,
        strength: float = 100,
        spot_size: float = 0.785398,
        spot_blend: float = 0.15,
        shadow_soft_size: float = 0.25,
        color: Vector3d = (1.0, 1.0, 1.0),
        cast_shadows=True,
        quaternion: Vector4d = (1, 0, 0, 0),
        translation: Vector3d = (0, 0, 0),
        tag=None
    ) -> SpotLight:
        """Add SpotLight light source to the scene

        Args:
            strength (float, optional): strength of the light source that light would emit over its entire area if
                it wasn't limited by the spot angle (default: 100)
            spot_size (float, optional): angle of the spotlight beam in [0.0174533, 3.14159] (default: 0.785398)
            spot_blend (float, optional): the softness of the spotlight edge in [0, 1] (default: 0.15)
            shadow_soft_size (float, optional): light size for ray shadow sampling (Raytraced shadows)
                in [0, inf] (default: 0.25)
            color (Vector3d, optional): color of the light source (default: (1.0, 1.0, 1.0))
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str, optional): name of the created collection in Blender to represent the point cloud.
                If None is passed the tag is automatically generated (default: None)

        Returns:
            SpotLight: created and added to the scene object
        """
        tag = self._process_tag(tag, "Spot")
        light = SpotLight(
            color=color, strength=strength, spot_size=spot_size, spot_blend=spot_blend, cast_shadows=cast_shadows,
            shadow_soft_size=shadow_soft_size, quaternion=quaternion, translation=translation, tag=tag
        )
        self._lights[tag] = light
        return light

    def add_area(
        self,
        shape: str,
        size: Union[float, Vector2d],
        strength: float = 100,
        color: Vector3d = (1.0, 1.0, 1.0),
        cast_shadows=True,
        quaternion: Vector4d = (1, 0, 0, 0),
        translation: Vector3d = (0, 0, 0),
        tag: str = None
    ) -> AreaLight:
        """Add AreaLight light source to the scene. Shape of the area is controlled by shape parameter

        Args:
            shape (str): type of the AreaLight, one of: [square, circle, rectangle, ellipse]
            size (Union[float, Vector2d]): size of the area of the area light for circle and square or
                [x, y] sizes of the area light for rectangle and ellipse
            strength (float, optional): strength of the light source emitted over the entire area of the light
                in all directions (default: 100)
            color (Vector3d, optional): color of the light source (default: (1.0, 1.0, 1.0))
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str, optional): name of the created collection in Blender to represent the point cloud.
                If None is passed the tag is automatically generated (default: None)

        Returns:
            AreaLight: subclass of AreaLight (depending on shape), created and added to the scene
        """
        tag = self._process_tag(tag, "Area")
        if shape == "square":
            light = SquareAreaLight(
                size=size, color=color, strength=strength, cast_shadows=cast_shadows,
                quaternion=quaternion, translation=translation, tag=tag
            )
        elif shape == "circle":
            light = CircleAreaLight(
                size=size, color=color, strength=strength, cast_shadows=cast_shadows,
                quaternion=quaternion, translation=translation, tag=tag
            )
        elif shape == "rectangle":
            light = RectangleAreaLight(
                size=size, color=color, strength=strength, cast_shadows=cast_shadows,
                quaternion=quaternion, translation=translation, tag=tag
            )
        elif shape == "ellipse":
            light = EllipseAreaLight(
                size=size, color=color, strength=strength, cast_shadows=cast_shadows,
                quaternion=quaternion, translation=translation, tag=tag
            )
        else:
            raise NotImplementedError(f"Unknown AreaLight shape: {shape}")
        self._lights[tag] = light
        return light

    def _process_tag(self, tag: str, default_prefix: str = "Light"):
        lights_keys = self._lights.keys()

        if tag is None:
            _tag = default_prefix + "_{:03d}"
            index = 0
            while _tag.format(index) in lights_keys:
                index += 1
            tag = _tag.format(index)
        elif tag in lights_keys:
            raise RuntimeError(f"Object with tag {tag} is already in collection.")

        return tag

    def keys(self):
        return self._lights.keys()

    def values(self):
        return self._lights.values()

    def items(self):
        return self._lights.items()

    def remove(self, obj_or_tag: Union[Light, str]):
        assert isinstance(obj_or_tag, (Light, str)), "Only Light object or it's tag is allowed"
        if isinstance(obj_or_tag, str):
            tag = obj_or_tag
        else:
            obj = obj_or_tag
            tag = obj.tag
        self.__delitem__(tag)

    def __getitem__(self, key: str) -> Light:
        return self._lights[key]

    def __delitem__(self, key: str):
        self._lights[key]._blender_remove_object()
        del self._lights[key]

    def __iter__(self) -> Iterable:
        return iter(self._lights)

    def __len__(self) -> int:
        return len(self._lights)

    def _reset(self):
        self._lights = dict()

    # def __str__(self):
    #     return str(self.__dict__)
    #
    # def __repr__(self):
    #     return '{}, D({})'.format(super(D, self).__repr__(), self.__dict__)
