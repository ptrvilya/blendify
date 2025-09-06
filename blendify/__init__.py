import bpy  # imported first to prepare internal Blender environment
import atexit
import os

from . import renderables
from .scene import Scene
from .internal.execution_decorator import _bpy_exit_bypassed

__all__ = [
    "scene",
    "__version__"
]

VERSION = (2, 1, 0)  # PEP 386
__version__ = ".".join([str(x) for x in VERSION])


def _force_exit():
    """
    This function is registered to be called on normal Python exit.
    It forces an immediate exit of the process.
    """
    global _bpy_exit_bypassed
    if not _bpy_exit_bypassed:
        # Flush standard output and error before hard exit
        try:
            import sys
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            pass
        # Using os._exit(0) is a hard exit, bypassing normal cleanup.
        os._exit(0)


def _setup_force_exit():
    """
    Sets up the environment and registers the exit handler.
    This is needed due to bug with Blender's memory leak detection on exit.
    """
    # Register the force-exit function to be called when the script ends
    atexit.register(_force_exit)


_setup_force_exit()
scene = Scene()
