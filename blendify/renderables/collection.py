from typing import Dict, Iterable

import numpy as np

from ..internal import Singleton
from ..renderables import Renderable, Mesh, PC, Material, Colors
from ..cameras import Camera


class RenderablesCollection(metaclass=Singleton):
    def __init__(self):
        self._renderables: Dict[str, Renderable] = dict()
        self.camera: Camera = None

    def add_pc(self, tag=None):
        tag = self._process_tag(tag, "PC")

    def add_camera_colored_pc(self, tag=None):
        tag = self._process_tag(tag, "Camera_Colored_PC")

        if self.camera is None:
            pass

    def add_mesh(self, vertices: np.ndarray, faces: np.ndarray, material: Material, colors: Colors, tag=None):
        tag = self._process_tag(tag, "Mesh")
        self._renderables[tag] = Mesh(vertices, faces, material, colors, tag)

    def add_primitive(self, tag=None):
        tag = self._process_tag(tag, "Primitive")

    def update_camera(self, camera: Camera):
        self.camera = camera
        for renderable in self._renderables.values():
            renderable.update_camera(camera)

    def _process_tag(self, tag: str, default_prefix:str = "Renderable"):
        renderable_keys = self._renderables.keys()

        if tag is None:
            _tag = default_prefix + "_{03d}"
            index = 0
            while _tag.format(index) in renderable_keys:
                index += 1
            tag = _tag
        elif tag in renderable_keys:
            raise RuntimeError(f"Object with tag {tag} is already in collection.")

        return tag

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
