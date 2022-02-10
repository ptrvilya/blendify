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
        assert (np.ndim(vertex_colors) == 2 and 3 <= vertex_colors.shape[1] <= 4), \
                f"Expected colors array of shape (N,3) or (N,4) got shape {vertex_colors.shape}"
        assert vertex_colors.dtype in [np.float32, np.float64],\
            "Colors shoud be stored as floating point numbers (np.float32 or np.float64)"
        assert np.all(vertex_colors >= 0) and np.all(vertex_colors <= 1), "Colors should be in range [0.0, 1.0]"
        self._vertex_colors = vertex_colors

    @property
    def vertex_colors(self) -> np.ndarray:
        return self._vertex_colors


class UniformColors(Colors):
    def __init__(self, uniform_color: Union[np.ndarray, Sequence[float]]):
        super().__init__()
        uniform_color = np.array(uniform_color)
        assert len(uniform_color) == 3, "Color should be in RGB format"
        assert uniform_color.max() <= 1. and uniform_color.min() >= 0., "Color values should be in [0,1] range"
        self._color = uniform_color

    @property
    def color(self) -> np.ndarray:
        return self._color


class UVMap(ABC):
    @abstractmethod
    def __init__(self, data: np.ndarray):
        self._data = data

    @property
    def data(self) -> np.ndarray:
        return self._data


class VertexUV(UVMap):
    def __init__(self, data: np.ndarray):
        super().__init__(data)


class FacesUV(UVMap):
    def __init__(self, data: np.ndarray):
        super().__init__(data)


class UVColors(Colors):
    @abstractmethod
    def __init__(self, uv_map: UVMap):
        super().__init__()
        self._uv_map = uv_map

    @property
    def uv_map(self) -> UVMap:
        return self._uv_map


class TextureColors(UVColors):
    def __init__(self, texture: np.ndarray, uv_map: UVMap):
        super().__init__(uv_map)
        if texture.dtype == np.uint8:
            texture = texture.astype(np.float32)/255.
        blender_image = bpy.data.images.new(name="tex_image", width=texture.shape[1],
                                            height=texture.shape[0])
        _copy_values_to_image(texture.reshape(-1, 3), blender_image.name)
        self._texture = blender_image

    @property
    def texture(self) -> UVMap:
        return self._texture


class FileTextureColors(UVColors):
    def __init__(self, texture_path: str, uv_map: UVMap):
        super().__init__(uv_map)
        self._texture = bpy.data.images.load(texture_path)

    @property
    def texture(self) -> UVMap:
        return self._texture
