from typing import Dict, Iterable, Union

from ..internal import Singleton
from ..internal.types import Vector2df, Vector3d, Vector4d
from .base import Light, PointLight, DirectionalLight, SpotLight,  \
    SquareAreaLight, CircleAreaLight, RectangleAreaLight, EllipseAreaLight


class LightsCollection(metaclass=Singleton):
    def __init__(self):
        self._lights: Dict[str, Light] = dict()

    def add_point(self, quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0),
                  color: Vector3d = (1.0, 1.0, 1.0), strength: float = 100,
                  shadow_soft_size: float = 0.25, tag=None, cast_shadows=True):
        # shadow_soft_size: Light size for ray shadow sampling (Raytraced shadows), [0, +inf)
        tag = self._process_tag(tag, "Point")
        self._lights[tag] = PointLight(color, strength, shadow_soft_size, tag, cast_shadows,
                                       quaternion, translation)

    def add_sun(self, quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0),
                color: Vector3d = (1.0, 1.0, 1.0), strength: float = 100,
                angular_diameter: float = 0.00918043, tag=None, cast_shadows=True):
        # angular_diameter: Angular diameter of the Sun as seen from the Earth,  [0, 3.14159]
        tag = self._process_tag(tag, "Sun")
        self._lights[tag] = DirectionalLight(color, strength, angular_diameter, tag,
                                             cast_shadows, quaternion, translation)

    def add_spot(self, quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0),
                 color: Vector3d = (1.0, 1.0, 1.0), strength: float = 100, spot_size: float = 0.785398,
                 spot_blend: float = 0.15, shadow_soft_size: float = 0.25, tag=None, cast_shadows=True):
        tag = self._process_tag(tag, "Spot")
        self._lights[tag] = SpotLight(color, strength, spot_size, spot_blend, shadow_soft_size,
                                      tag, cast_shadows, quaternion, translation)

    def add_area(self, shape: str, size: Union[float, Vector2df],
                 quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0),
                 color: Vector3d = (1.0, 1.0, 1.0), strength: float = 100, tag=None, cast_shadows=True):
        tag = self._process_tag(tag, "Area")
        if shape == "square":
            self._lights[tag] = SquareAreaLight(size, color, strength, tag, cast_shadows, quaternion, translation)
        elif shape == "circle":
            self._lights[tag] = CircleAreaLight(size, color, strength, tag, cast_shadows, quaternion, translation)
        elif shape == "rectangle":
            self._lights[tag] = RectangleAreaLight(size, color, strength, tag, cast_shadows, quaternion, translation)
        elif shape == "ellipse":
            self._lights[tag] = EllipseAreaLight(size, color, strength, tag, cast_shadows, quaternion, translation)
        else:
            raise RuntimeError(f"Unknown AreaLight shape: {shape}")

    def _process_tag(self, tag: str, default_prefix:str = "Light"):
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

    def __getitem__(self, key: str) -> Light:
        return self._lights[key]

    def __setitem__(self, key: str, value: Light):
        self._lights[key] = value

    def __delitem__(self, key: str):
        del self.__dict__[key]

    def __iter__(self) -> Iterable:
        return iter(self._lights)

    def __len__(self) -> int:
        return len(self._lights)

    # def __str__(self):
    #     return str(self.__dict__)
    #
    # def __repr__(self):
    #     return '{}, D({})'.format(super(D, self).__repr__(), self.__dict__)
