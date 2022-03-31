from abc import ABC, abstractmethod
from typing import Tuple

import bpy


class Material(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def create_material(self, name: str = "object_material") -> Tuple[bpy.types.Material, bpy.types.ShaderNode]:
        pass


def material_property(name: str):
    """Creates a property for the material class to get one of the material parameters

    Args:
        name (str): property name

    Returns:
        property: A class property with defines parameter setting and getting behaviour
    """
    name = "_" + name

    def getter(obj):
        return getattr(obj, name)

    return property(getter)
