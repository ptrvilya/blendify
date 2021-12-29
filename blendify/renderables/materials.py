import bpy
import numpy as np
from abc import ABC, abstractmethod
from typing import Union, Tuple, List, Sequence


class Material(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def create_material(self, name: str = "object_material") -> Tuple[bpy.types.Material, bpy.types.ShaderNode]:
        pass


class PrinsipledBSDFMaterial:
    def __init__(self):
        self.spec_intensity = 0.3
        self.alpha = 1.

    def create_material(self, name: str = "object_material") \
            -> Tuple[bpy.types.Material, bpy.types.ShaderNodeBsdfPrincipled]:
        object_material = bpy.data.materials.new(name=name)
        object_material.use_nodes = True
        bsdf_node = object_material.node_tree.nodes["Principled BSDF"]

        bsdf_node.inputs['Alpha'].default_value = self.alpha  # Set alpha
        bsdf_node.inputs['Specular'].default_value = self.spec_intensity

        return object_material, bsdf_node
