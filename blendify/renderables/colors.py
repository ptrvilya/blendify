import bpy
import numpy as np
from abc import ABC, abstractmethod
from typing import Union, Tuple, List, Sequence
from ..internal.texture import _copy_values_to_image


class Colors(ABC):
    @abstractmethod
    def __init__(self):
        pass


class VertexColors(Colors):
    def __init__(self, vertex_colors: np.ndarray):
        super().__init__()
        self.vertex_colors = vertex_colors


class UniformColors(Colors):
    def __init__(self, uniform_color: Union[np.ndarray, Sequence[float]]):
        super().__init__()
        self.color = uniform_color

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, uniform_color):
        uniform_color = np.array(uniform_color)
        assert len(uniform_color) == 3, "Color should be in RGB format"
        assert uniform_color.max() <= 1. and uniform_color.min() >= 0., "Color values should be in [0,1] range"
        self._color = uniform_color


class UVMap(ABC):
    @abstractmethod
    def __init__(self, data: np.ndarray):
        self.data = data


class VertexUV(UVMap):
    def __init__(self, data: np.ndarray):
        self.data = data


class FacesUV(UVMap):
    def __init__(self, data: np.ndarray):
        self.data = data

class UVColors(Colors):
    @abstractmethod
    def __init__(self, uv_map: UVMap):
        super().__init__()
        self.uv_map = uv_map


class TextureColors(UVColors):
    def __init__(self, texture: np.ndarray, uv_map: UVMap):
        super().__init__(uv_map)
        if texture.dtype == np.uint8:
            texture = texture.astype(np.float32)/255.
        blender_image = bpy.data.images.new(name="tex_image", width=texture.shape[1],
                                            height=texture.shape[0])
        _copy_values_to_image(texture.reshape(-1, 3), blender_image.name)
        self.texture = blender_image


class FileTextureColors(UVColors):
    def __init__(self, texture_path: str, uv_map: UVMap):
        super().__init__(uv_map)
        self.texture = bpy.data.images.load(texture_path)
