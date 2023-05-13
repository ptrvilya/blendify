import bpy  # imported first to prepare internal Blender environment
from . import renderables
from .scene import Scene

__all__ = [
    "scene",
    "__version__"
]

VERSION = (1, 2, 2)  # PEP 386
__version__ = ".".join([str(x) for x in VERSION])

scene = Scene()


def _get_scene():
    return scene
