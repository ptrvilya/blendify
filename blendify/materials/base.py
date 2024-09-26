from abc import ABC, abstractmethod
from typing import Sequence, Union, Dict, Optional
from dataclasses import dataclass

import bpy


@dataclass
class MaterialInstance:
    blender_material: bpy.types.Material
    inputs: Dict[str, bpy.types.NodeSocket]
    colors_node: Optional[bpy.types.ShaderNode] = None


class Material(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def create_material(self, name: str = "object_material") -> MaterialInstance:
        pass


MaterialList = Sequence[Material]


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
