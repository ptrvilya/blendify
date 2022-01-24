from typing import Dict, Iterable

import numpy as np

from ..internal import Singleton
from ..internal.types import Vector3d, Vector4d
from .base import Renderable
from .mesh import Mesh
from .pointcloud import PointCloud
from .colors import Colors
from . import primitives
from .materials import Material
from ..cameras import Camera


class RenderablesCollection(metaclass=Singleton):
    def __init__(self):
        self._renderables: Dict[str, Renderable] = dict()
        self.camera: Camera = None

    def add_pc(self, vertices: np.ndarray, material: Material, colors: Colors, point_size: float = 0.006,
               base_primitive: str = "CUBE", add_particle_color_emission: bool = True, tag=None) -> PointCloud:
        tag = self._process_tag(tag, "PC")
        obj = PointCloud(vertices, material, colors, tag, point_size,
                         base_primitive, add_particle_color_emission)
        self._renderables[tag] = obj
        return obj

    def add_camera_colored_pc(self, tag=None):
        tag = self._process_tag(tag, "Camera_Colored_PC")

        if self.camera is None:
            pass

    def add_mesh(self, vertices: np.ndarray, faces: np.ndarray, material: Material, colors: Colors, tag=None) -> Mesh:
        tag = self._process_tag(tag, "Mesh")
        obj = Mesh(vertices, faces, material, colors, tag)
        self._renderables[tag] = obj
        return obj

    def add_ellipsoid_nurbs(self, radius: Vector3d, material: Material, colors: Colors,
                            quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0), tag=None):
        tag = self._process_tag(tag, "Ellipsoid")
        obj = primitives.EllipsoidNURBS(radius, material, colors, tag, quaternion, translation)
        self._renderables[tag] = obj
        return obj

    def add_sphere_nurbs(self, radius: float, material: Material, colors: Colors,
                         quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0), tag=None):
        tag = self._process_tag(tag, "Sphere")
        obj = primitives.SphereNURBS(radius, material, colors, tag, quaternion, translation)
        self._renderables[tag] = obj
        return obj

    def add_curve_nurbs(self, keypoints: np.ndarray, radius: float, material: Material, colors: Colors,
                        quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0), tag=None):
        tag = self._process_tag(tag, "Curve")
        obj = primitives.CurveNURBS(keypoints, radius, material, colors, tag, quaternion, translation)
        self._renderables[tag] = obj
        return obj

    def add_circle_mesh(self, radius: float, material: Material, colors: Colors, vertices: int = 32,
                        fill_type: str = "NGON", quaternion: Vector4d = (1, 0, 0, 0),
                        translation: Vector3d = (0, 0, 0), tag=None):
        tag = self._process_tag(tag, "Circle")
        obj = primitives.CircleMesh(radius, material, colors, tag, vertices, fill_type, quaternion, translation)
        self._renderables[tag] = obj
        return obj

    def add_cylinder_mesh(self, radius: float, height: float, material: Material, colors: Colors,
                          vertices: int = 32, fill_type: str = "NGON", quaternion: Vector4d = (1, 0, 0, 0),
                          translation: Vector3d = (0, 0, 0), tag=None):
        tag = self._process_tag(tag, "Cylinder")
        obj = primitives.CylinderMesh(radius, height, material, colors, tag,
                                      vertices, fill_type, quaternion, translation)
        self._renderables[tag] = obj
        return obj

    def update_camera(self, camera: Camera):
        self.camera = camera
        for renderable in self._renderables.values():
            renderable.update_camera(camera)

    def _process_tag(self, tag: str, default_prefix: str = "Renderable"):
        renderable_keys = self._renderables.keys()

        if tag is None:
            _tag = default_prefix + "_{:03d}"
            index = 0
            while _tag.format(index) in renderable_keys:
                index += 1
            tag = _tag.format(index)
        elif tag in renderable_keys:
            raise RuntimeError(f"Object with tag {tag} is already in collection.")

        return tag

    def keys(self):
        return self._renderables.keys()

    def values(self):
        return self._renderables.values()

    def items(self):
        return self._renderables.items()

    def __getitem__(self, key: str) -> Renderable:
        return self._renderables[key]

    def __setitem__(self, key: str, value: Renderable):
        self._renderables[key] = value

    def __delitem__(self, key: str):
        del self.__dict__[key]

    def __iter__(self) -> Iterable:
        return iter(self._renderables)

    def __len__(self) -> int:
        return len(self._renderables)
