import bpy
from . import renderables
from .scene import Scene

__all__ = [
    "get_scene",
    "__version__"
]

VERSION = (1, 0, 0)  # PEP 386
__version__ = ".".join([str(x) for x in VERSION])

_scene = Scene()


def get_scene():
    return _scene
