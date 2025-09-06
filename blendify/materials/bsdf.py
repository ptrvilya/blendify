from typing import Tuple

import bpy

from .base import Material, material_property, MaterialInstance
from .wireframe import WireframeMaterial


class PrincipledBSDFMaterial(Material):
    """A class which manages the parameters of PrincipledBSDF Blender material.
    Full docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/principled.html
    """

    def __init__(
            self, alpha=1.0, anisotropic=0.0, anisotropic_rotation=0.0, coat_ior=0.0, coat_roughness=0.0,
            coat_tint=(1.0, 1.0, 1.0, 1.0), coat_weight=0.0, diffuse_roughness=0.0, emission_color=(0, 0, 0, 0),
            emission_strength=0.0, ior=1.45, metallic=0.0, roughness=0.4, sheen_weight=0.0, sheen_roughness=0.5,
            sheen_tint=(0.5, 0.5, 0.5, 1.0), specular_ior=0.3, specular_tint=(0.0, 0.0, 0.0, 1.0),
            subsurface_anisotropy=0.0, subsurface_radius=(1.0, 0.2, 1.0), subsurface_scale=0.05, subsurface_weight=0.0,
            thin_film_ior=1.33, thin_film_thickness=0.0, transmission_weight=0.0,
    ):
        super().__init__()
        self._property2blender_mapping = {
            # alpha
            "alpha": "Alpha",
            # anisotropic
            "anisotropic": "Anisotropic", "anisotropic_rotation": "Anisotropic Rotation",
            # clearcoat
            "coat_ior": "Coat IOR", "coat_roughness": "Coat Roughness",
            "coat_weight": "Coat Weight", "coat_tint": "Coat Tint",
            # diffuse
            "diffuse_roughness": "Diffuse Roughness",
            # emission
            "emission_color": "Emission Color", "emission_strength": "Emission Strength",
            # general material
            "ior": "IOR", "metallic": "Metallic", "roughness": "Roughness",
            # sheen
            "sheen_weight": "Sheen Weight", "sheen_roughness": "Sheen Roughness", "sheen_tint": "Sheen Tint",
            # specular
            "specular_ior": "Specular IOR Level", "specular_tint": "Specular Tint",
            # subsurface (random walk)
            "subsurface_anisotropy": "Subsurface Anisotropy", "subsurface_radius": "Subsurface Radius",
            "subsurface_scale": "Subsurface Scale", "subsurface_weight": "Subsurface Weight",
            # thin film
            "thin_film_ior": "Thin Film IOR", "thin_film_thickness": "Thin Film Thickness",
            # transmission
            "transmission_weight": "Transmission Weight",

        }
        for argname, argvalue in locals().items():
            if argname in self._property2blender_mapping.keys():
                self.__setattr__(argname, material_property(argname))
                self.__setattr__("_" + argname, argvalue)

    def create_material(self, name: str = "object_material") -> MaterialInstance:
        """Create the Blender material with the parameters stored in the current object

        Args:
            name (str): a unique material name for Blender

        Returns:
            Tuple[bpy.types.Material, bpy.types.ShaderNodeBsdfPrincipled]: Blender material and the
                shader node which uses the created material
        """

        object_material = bpy.data.materials.new(name=name)
        object_material.use_nodes = True
        bsdf_node = object_material.node_tree.nodes["Principled BSDF"]
        material_instance = MaterialInstance(blender_material=object_material,
                                             inputs={"Color": bsdf_node.inputs["Base Color"], "Alpha": bsdf_node.inputs["Alpha"],
                                                     "Emission Color": bsdf_node.inputs["Emission Color"],
                                                     "Emission Strength": bsdf_node.inputs["Emission Strength"]})

        # Set material properties
        for property_name, blender_name in self._property2blender_mapping.items():
            bsdf_node.inputs[blender_name].default_value = self.__getattribute__("_" + property_name)

        return material_instance


class GlossyBSDFMaterial(Material):
    """A class which manages the parameters of GlossyBSDF Blender material.
    Full docs: https://docs.blender.org/manual/en/latest/render/shader_nodes/shader/glossy.html
    """

    def __init__(self, roughness=0.4, distribution="GGX"):
        super().__init__()
        self.roughness, self._roughness = material_property("roughness"), roughness
        self._distribution = distribution

    def create_material(self, name: str = "object_material") -> MaterialInstance:
        """Create the Blender material with the parameters stored in the current object

        Args:
            name (str): a unique material name for Blender

        Returns:
            Tuple[bpy.types.Material, bpy.types.ShaderNodeBsdfGlossy]: Blender material and the
                shader node which uses the created material
        """

        object_material = bpy.data.materials.new(name=name)
        object_material.use_nodes = True
        material_nodes = object_material.node_tree.nodes

        bsdf_node = material_nodes.new("ShaderNodeBsdfGlossy")
        material_nodes.remove(material_nodes['Principled BSDF'])
        object_material.node_tree.links.new(material_nodes["Material Output"].inputs["Surface"],
                                            bsdf_node.outputs[0])
        # Set material properties
        bsdf_node.inputs["Roughness"].default_value = self._roughness
        bsdf_node.distribution = self._distribution

        material_instance = MaterialInstance(blender_material=object_material,
                                             inputs={"Color": bsdf_node.inputs["Color"]})

        return material_instance

    @property
    def distribution(self):
        return self._distribution


class PrincipledBSDFWireframeMaterial(WireframeMaterial, PrincipledBSDFMaterial):
    def __init__(
            self, wireframe_thickness=0.01, wireframe_color=(0., 0., 0., 1.), **kwargs
    ):
        super().__init__(
            wireframe_thickness=wireframe_thickness, wireframe_color=wireframe_color, **kwargs
        )

    def create_material(self, name: str = "object_material") -> MaterialInstance:
        object_material = bpy.data.materials.new(name=name)
        object_material.use_nodes = True
        material_nodes = object_material.node_tree.nodes

        # Create BSDF
        bsdf_node = object_material.node_tree.nodes["Principled BSDF"]

        # Set BSDF properties
        for property_name, blender_name in self._property2blender_mapping.items():
            bsdf_node.inputs[blender_name].default_value = self.__getattribute__("_" + property_name)

        # Create and link wireframe
        self.overlay_wireframe(object_material, bsdf_node)

        # Create internal representation
        material_instance = MaterialInstance(
            blender_material=object_material,
            inputs={
                "Color": bsdf_node.inputs["Base Color"],
                "Alpha": bsdf_node.inputs["Alpha"],
                "Emission Color": bsdf_node.inputs["Emission Color"],
                "Emission Strength": bsdf_node.inputs["Emission Strength"]
            }
        )

        return material_instance
