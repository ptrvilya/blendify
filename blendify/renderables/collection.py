from typing import Dict, Iterable

from ..internal import Singleton
from ..renderables import Renderable
from ..cameras import Camera


class RenderablesCollection(metaclass=Singleton):
    def __init__(self):
        self._renderables: Dict[str, Renderable] = dict()
        self.camera: Camera = None

    def add_pc(self):
        pass

    def add_camera_colored_pc(self):
        if self.camera is None:
            pass

    def add_mesh(self):
        pass

    def add_primitive(self):
        pass

    def update_camera(self, camera: Camera):
        self.camera = camera
        for renderable in self._renderables.values():
            renderable.update_camera(camera)

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
