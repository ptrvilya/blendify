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
    """
        Full docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html
    """
    def __init__(self, metallic=0.0, specular=0.3, specular_tint=0.0, roughness=0.4, anisotropic=0.0,
                 anisotropic_rotation=0.0, sheen=0.0, sheen_tint=0.5, clearcoat=0.0, clearcoat_roughness=0.0,
                 ior=1.45, transmission=0.0, transmission_roughness=0.0, emission=(0, 0, 0, 0),
                 emission_strength=0.0, alpha=1.0):
        self.metallic = metallic
        self.specular = specular
        self.specular_tint = specular_tint
        self.roughness = roughness
        self.anisotropic = anisotropic
        self.anisotropic_rotation = anisotropic_rotation
        self.sheen = sheen
        self.sheen_tint = sheen_tint
        self.clearcoat = clearcoat
        self.clearcoat_roughness = clearcoat_roughness
        self.ior = ior
        self.transmission = transmission
        self.transmission_roughness = transmission_roughness
        self.emission = emission
        self.emission_strength = emission_strength
        self.alpha = alpha

    def create_material(self, name: str = "object_material") \
            -> Tuple[bpy.types.Material, bpy.types.ShaderNodeBsdfPrincipled]:
        object_material = bpy.data.materials.new(name=name)
        object_material.use_nodes = True
        bsdf_node = object_material.node_tree.nodes["Principled BSDF"]

        # Set material properties
        bsdf_node.inputs['Metallic'].default_value = self.metallic
        bsdf_node.inputs['Specular'].default_value = self.specular
        bsdf_node.inputs['Specular Tint'].default_value = self.specular_tint
        bsdf_node.inputs['Roughness'].default_value = self.roughness
        bsdf_node.inputs['Anisotropic'].default_value = self.anisotropic
        bsdf_node.inputs['Anisotropic Rotation'].default_value = self.anisotropic_rotation
        bsdf_node.inputs['Sheen'].default_value = self.sheen
        bsdf_node.inputs['Sheen Tint'].default_value = self.sheen_tint
        bsdf_node.inputs['Clearcoat'].default_value = self.clearcoat
        bsdf_node.inputs['Clearcoat Roughness'].default_value = self.clearcoat_roughness
        bsdf_node.inputs['IOR'].default_value = self.ior
        bsdf_node.inputs['Transmission'].default_value = self.transmission
        bsdf_node.inputs['Transmission Roughness'].default_value = self.transmission_roughness
        bsdf_node.inputs['Emission'].default_value = self.emission
        bsdf_node.inputs['Emission Strength'].default_value = self.emission_strength
        bsdf_node.inputs['Alpha'].default_value = self.alpha

        return object_material, bsdf_node
