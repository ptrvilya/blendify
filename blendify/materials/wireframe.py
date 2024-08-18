from typing import Tuple

import bpy

from .base import Material


class WireframeMaterial(Material):
    def __init__(
        self, wireframe_thickness=0.01, wireframe_color=(0., 0., 0., 1.), **kwargs
    ):
        super().__init__(**kwargs)

        self._wireframe_thickness = wireframe_thickness
        self._wireframe_color = wireframe_color

    def overlay_wireframe(self, object_material, base_material_node):
        material_nodes = object_material.node_tree.nodes

        # Create material for wireframe
        wireframe_color_node = material_nodes.new("ShaderNodeRGB")
        wireframe_color_node.outputs["Color"].default_value = self._wireframe_color
        bc_node = material_nodes.new("ShaderNodeBrightContrast")
        object_material.node_tree.links.new(bc_node.inputs["Color"],
                                            wireframe_color_node.outputs["Color"])
        diffuse_node = material_nodes.new("ShaderNodeBsdfDiffuse")
        object_material.node_tree.links.new(diffuse_node.inputs["Color"],
                                            bc_node.outputs["Color"])

        # Create wireframe and mix it with base material
        wireframe_node = material_nodes.new("ShaderNodeWireframe")
        wireframe_node.inputs[0].default_value = self._wireframe_thickness  # thickness
        mix_node = material_nodes.new("ShaderNodeMixShader")

        object_material.node_tree.links.new(mix_node.inputs["Fac"],
                                            wireframe_node.outputs["Fac"])
        object_material.node_tree.links.new(mix_node.inputs[1],
                                            base_material_node.outputs[0])
        object_material.node_tree.links.new(mix_node.inputs[2],
                                            diffuse_node.outputs[0])

        object_material.node_tree.links.new(material_nodes["Material Output"].inputs["Surface"],
                                            mix_node.outputs[0])
