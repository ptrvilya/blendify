import bpy
import numpy as np
from abc import ABC, abstractmethod
from typing import Union, Tuple, List, Sequence


class Visuals(ABC):
    def __init__(self):
        self.spec_intensity = 0.3
        self.alpha = 1.
        self._blender_material = None

    def _create_blender_matbsdf(self) -> Tuple[bpy.types.Material, bpy.types.ShaderNodeBsdfPrincipled]:
        object_material = bpy.data.materials.new('object_material')
        object_material.use_nodes = True
        bsdf = object_material.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Alpha'].default_value = self.alpha  # Set alpha
        bsdf.inputs['Specular'].default_value = self.spec_intensity
        return object_material, bsdf

    @abstractmethod
    def create_material(self) -> bpy.types.Material:
        pass


class VertexColorVisuals(Visuals):
    def __init__(self, vertex_colors: np.ndarray):
        super().__init__()
        self.vertex_colors = vertex_colors

    def create_material(self) -> bpy.types.Material:
        object_material, bsdf = self._create_blender_matbsdf()
        vertex_color = object_material.node_tree.nodes.new('ShaderNodeVertexColor')
        object_material.node_tree.links.new(vertex_color.outputs[0], bsdf.inputs[0])
        return object_material


class UniformColorVisuals(Visuals):
    def __init__(self, uniform_color: Union[np.ndarray, Sequence[float]]):
        super().__init__()
        self.color = uniform_color

    def create_material(self) -> bpy.types.Material:
        object_material, bsdf = self._create_blender_matbsdf()
        color_node = object_material.node_tree.nodes.new('ShaderNodeRGB')
        color_node.outputs[0].default_value = self.color.tolist() + [1.]
        object_material.node_tree.links.new(color_node.outputs[0], bsdf.inputs[0])
        return object_material

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, uniform_color):
        uniform_color = np.array(uniform_color)
        assert len(uniform_color) == 3, "Color should be in RGB format"
        assert uniform_color.max() <= 1. and uniform_color.min() >= 0., "Color values should be in [0,1] range"
        self._color = uniform_color


class UVVisuals(Visuals):
    @abstractmethod
    def __init__(self, uv_map: np.ndarray):
        super().__init__()
        self.uv_map = uv_map


class TextureVisuals(UVVisuals):
    def __init__(self, texture: np.ndarray, uv_map: np.ndarray):
        super().__init__(uv_map)
        self.texture = texture

    def create_material(self) -> bpy.types.Material:
        object_material, bsdf = self._create_blender_matbsdf()
        object_texture = object_material.node_tree.nodes.new('ShaderNodeTexImage')
        object_material.node_tree.links.new(bsdf.inputs['Base Color'], object_texture.outputs['Color'])
        raise NotImplementedError("Assigning textures from memory is not implemented yet")


class FileTextureVisuals(UVVisuals):
    def __init__(self, texture_path: str, uv_map: np.ndarray):
        super().__init__(uv_map)
        self.texture_path = texture_path

    def create_material(self) -> bpy.types.Material:
        object_material, bsdf = self._create_blender_matbsdf()
        object_texture = object_material.node_tree.nodes.new('ShaderNodeTexImage')
        object_texture.image = self.texture_path
        object_material.node_tree.links.new(bsdf.inputs['Base Color'], object_texture.outputs['Color'])
        return object_material
