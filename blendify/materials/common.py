from typing import Tuple

import bpy

from .base import Material, material_property


class PrinsipledBSDFMaterial(Material):
    """A class which manages the parameters of PrinsipledBSDF Blender material.
    Full docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html
    """

    def __init__(
            self, metallic=0.0, specular=0.3, specular_tint=0.0, roughness=0.4, anisotropic=0.0,
            anisotropic_rotation=0.0,
            sheen=0.0, sheen_tint=0.5, clearcoat=0.0, clearcoat_roughness=0.0, ior=1.45, transmission=0.0,
            transmission_roughness=0.0, emission=(0, 0, 0, 0), emission_strength=0.0, alpha=1.0
    ):
        super().__init__()
        self._property2blender_mapping = {
            "metallic": "Metallic", "specular": "Specular", "specular_tint": "Specular Tint", "roughness": "Roughness",
            "anisotropic": "Anisotropic", "anisotropic_rotation": "Anisotropic Rotation", "sheen": "Sheen",
            "sheen_tint": "Sheen Tint", "clearcoat": "Clearcoat", "clearcoat_roughness": "Clearcoat Roughness",
            "ior": "IOR", "transmission": "Transmission", "transmission_roughness": "Transmission Roughness",
            "emission": "Emission", "emission_strength": "Emission Strength", "alpha": "Alpha"
        }
        for argname, argvalue in locals().items():
            if argname in self._property2blender_mapping.keys():
                self.__setattr__(argname, material_property(argname))
                self.__setattr__("_" + argname, argvalue)

        self._object_material = None
        self._bsdf_node = None

    def create_material(self, name: str = "object_material") \
            -> Tuple[bpy.types.Material, bpy.types.ShaderNodeBsdfPrincipled]:
        """Create the Blender material with the parameters stored in the current object

        Args:
            name (str): a unique material name for Blender

        Returns:
            Tuple[bpy.types.Material, bpy.types.ShaderNodeBsdfPrincipled]: Blender material and the
                shader node which uses the created material
        """
        # This anti-duplicate check causes error as of now, so it was commented out until a proper fix
        # if self._object_material is not None and self._bsdf_node is not None:
        #     return self._object_material, self._bsdf_node

        self._object_material = bpy.data.materials.new(name=name)
        self._object_material.use_nodes = True
        self._bsdf_node = self._object_material.node_tree.nodes["Principled BSDF"]

        # Set material properties
        for property_name, blender_name in self._property2blender_mapping.items():
            self._bsdf_node.inputs[blender_name].default_value = self.__getattribute__("_" + property_name)

        return self._object_material, self._bsdf_node


class GlossyBSDFMaterial(Material):
    """A class which manages the parameters of GlossyBSDF Blender material.
    Full docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/glossy.html
    """

    def __init__(self, roughness=0.4, distribution="GGX"):
        super().__init__()
        self.roughness, self._roughness = material_property("roughness"), roughness
        self._distribution = distribution

        self._object_material = None
        self._bsdf_node = None

    def create_material(self, name: str = "object_material") \
            -> Tuple[bpy.types.Material, bpy.types.ShaderNodeBsdfGlossy]:
        """Create the Blender material with the parameters stored in the current object

        Args:
            name (str): a unique material name for Blender

        Returns:
            Tuple[bpy.types.Material, bpy.types.ShaderNodeBsdfGlossy]: Blender material and the
                shader node which uses the created material
        """
        # This anti-duplicate check causes error as of now, so it was commented out until a proper fix
        # if self._object_material is not None and self._bsdf_node is not None:
        #     return self._object_material, self._bsdf_node

        self._object_material = bpy.data.materials.new(name=name)
        self._object_material.use_nodes = True
        material_nodes = self._object_material.node_tree.nodes

        self._bsdf_node = material_nodes.new("ShaderNodeBsdfGlossy")
        material_nodes.remove(material_nodes['Principled BSDF'])
        self._object_material.node_tree.links.new(material_nodes["Material Output"].inputs["Surface"],
                                                  self._bsdf_node.outputs[0])
        # Set material properties
        self._bsdf_node.inputs["Roughness"].default_value = self._roughness
        self._bsdf_node.distribution = self._distribution

        return self._object_material, self._bsdf_node

    @property
    def distribution(self):
        return self._distribution
