import numpy as np
import bpy_types
from abc import ABC, abstractmethod
from .internal.positionable import Positionable

class Camera(Positionable):
    @abstractmethod
    def __init__(self, tag: str, blender_object: bpy_types.Object):
        super().__init__(tag, blender_object)
