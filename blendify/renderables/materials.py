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


class PrinsipledBSDFMaterial:
    """A class which manages the parameters of PrinsipledBSDF Blender material.
    Full docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html
    """
    def __init__(
        self, metallic=0.0, specular=0.3, specular_tint=0.0, roughness=0.4, anisotropic=0.0, anisotropic_rotation=0.0,
        sheen=0.0, sheen_tint=0.5, clearcoat=0.0, clearcoat_roughness=0.0, ior=1.45, transmission=0.0,
        transmission_roughness=0.0, emission=(0, 0, 0, 0), emission_strength=0.0, alpha=1.0
    ):
        self._property2blender_mapping = {
            "metallic": "Metallic", "specular": "Specular", "specular_tint": "Specular Tint", "roughness": "Roughness",
            "anisotropic": "Anisotropic", "anisotropic_rotation": "Anisotropic Rotation", "sheen": "Sheen",
            "sheen_tint": "Sheen Tint", "clearcoat": "Clearcoat", "clearcoat_roughness": "Clearcoat Roughness",
            "ior": "IOR", "transmission": "Transmission", "transmission_roughness": "Transmission Roughness",
            "emission": "Emission", "emission_strength": "Emission Strength", "alpha": "Alpha"
        }
        for argname, argvalue in locals().items():
            if argname == "self":
                continue
            self.__setattr__(argname, material_property(argname, self._property2blender_mapping[argname]))
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


class GlossyBSDFMaterial:
    """A class which manages the parameters of GlossyBSDF Blender material.
    Full docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/glossy.html
    """
    def __init__(self, roughness=0.4, distribution="GGX"):
        self.roughness, self._roughness = material_property("roughness", "Roughness"), roughness
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
        if self._object_material is not None and self._bsdf_node is not None:
            return self._object_material, self._bsdf_node

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

    @distribution.setter
    def distribution(self, value):
        self._distribution = value
        if self._object_material is not None and self._bsdf_node is not None:
            self._bsdf_node.distribution = self._distribution
