from abc import ABC, abstractmethod
from typing import Tuple

import bpy


class Material(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def create_material(self, name: str = "object_material") -> Tuple[bpy.types.Material, bpy.types.ShaderNode]:
        pass


def material_property(name: str, blender_name: str):
    """Creates a property for the material class to set and get one of the material parameters
    both in the class and in Blender

    Args:
        name (str): property name
        blender_name (str): a Blender parameter name to control

    Returns:
        property: A class property with defines parameter setting and getting behaviour
    """
    name = "_" + name

    def getter(obj):
        return getattr(obj, name)

    def setter(obj, new_value):
        _bsdf_node = getattr(obj, "_bsdf_node", None)
        _material = getattr(obj, "_object_material", None)
        if _bsdf_node is not None and _material is not None:
            _bsdf_node.inputs[blender_name].default_value = new_value
        setattr(obj, name, new_value)

    return property(getter, setter)
