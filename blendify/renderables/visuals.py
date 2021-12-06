import numpy as np
from abc import ABC
from typing import Union, Tuple, List, Sequence


class Visuals(ABC):
    def __init__(self):
        self.spec_intensity = 0.3
        self.alpha = 1.


class VertexColorVisuals(Visuals):
    def __init__(self, vertex_colors: np.ndarray):
        super().__init__()
        self.vertex_colors = vertex_colors


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
