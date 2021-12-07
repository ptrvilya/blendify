import bpy
import numpy as np
from abc import ABC, abstractmethod
from typing import Union, Tuple, List, Sequence


class Visuals(ABC):
    def __init__(self):
        self.spec_intensity = 0.3
        self.alpha = 1.
        self._blender_material = None

    def _create_blender_matbsdf(self):
        object_material = bpy.data.materials.new('object_material')
        object_material.use_nodes = True
        bsdf = object_material.node_tree.nodes["Principled BSDF"]
        bsdf.inputs['Alpha'].default_value = self.alpha  # Set alpha
        bsdf.inputs['Specular'].default_value = self.spec_intensity
        return object_material, bsdf

    @abstractmethod
    def create_material(self):
        pass


class VertexColorVisuals(Visuals):
    def __init__(self, vertex_colors: np.ndarray):
        super().__init__()
        self.vertex_colors = vertex_colors

    def create_material(self):
        object_material, bsdf = self._create_blender_matbsdf()
        vertex_color = object_material.node_tree.nodes.new('ShaderNodeVertexColor')
        object_material.node_tree.links.new(vertex_color.outputs[0], bsdf.inputs[0])
        return object_material


class UniformColorVisuals(Visuals):
    def __init__(self, uniform_color: Union[np.ndarray, Sequence[float]]):
        super().__init__()
        self.color = np.array(uniform_color)
        assert len(self.color) == 4, "Color should be in RGBA format"
        assert self.color.max() <= 1. and self.color.min() >= 0., "Color values should be in [0,1] range"


class UVVisuals(Visuals):
    def __init__(self, uv_map: np.ndarray):
        super().__init__()
        self.uv_map = uv_map


class TextureVisuals(UVVisuals):
    def __init__(self, texture: np.ndarray, uv_map: np.ndarray):
        super().__init__(uv_map)
        self.texture = texture


class FileTextureVisuals(UVVisuals):
    def __init__(self, texture_path: np.ndarray, uv_map: np.ndarray):
        super().__init__(uv_map)
        self.texture_path = texture_path
