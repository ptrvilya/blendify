from typing import Dict, Iterable

from ..internal import Singleton
from ..renderables import Renderable
from ..cameras import Camera


class RenderablesCollection(metaclass=Singleton):
    _renderables: Dict[str, Renderable] = dict()
    camera: Camera = None

    def __init__(self):
        pass

    @classmethod
    def add_pc(cls):
        pass

    @classmethod
    def add_camera_colored_pc(cls):
        pass

    @classmethod
    def add_mesh(cls):
        pass

    @classmethod
    def add_primitive(cls):
        pass

    @classmethod
    def update_camera(cls, camera: Camera):
        cls.camera = camera
        for renderable in cls._renderables.values():
            renderable.update_camera(camera)

    @classmethod
    def __getitem__(cls, key: str) -> Renderable:
        return cls._renderables[key]

    @classmethod
    def __setitem__(cls, key: str, value: Renderable):
        cls._renderables[key] = value

    @classmethod
    def __delitem__(cls, key: str):
        del cls.__dict__[key]

    @classmethod
    def __iter__(cls) -> Iterable:
        return iter(cls._renderables)

    @classmethod
    def __len__(cls) -> int:
        return len(cls._renderables)
