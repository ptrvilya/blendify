from scene import Scene

# TODO adjust __all__
# __all__ = [
#     "get_scene"
# ]

VERSION = (0, 0, 1)  # PEP 386
__version__ = ".".join([str(x) for x in VERSION])

_scene = Scene()


def get_scene():
    return _scene
