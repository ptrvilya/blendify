import numpy as np
from typing import Union

from .base import ColorsMetadata, Colors
from ..internal.types import Vector3d, Vector4d


class VertexColors(Colors):
    """A container which stores a color information for each vertex of an object
    (vertex colors are interpolated over the faces)
    """

    def __init__(self, vertex_colors: np.ndarray):
        """Create the vertex color container

        Args:
            vertex_colors (np.ndarray): numpy array of size (N,3) for RGB or (N,4) for RGBD colors
        """
        super().__init__()
        assert (np.ndim(vertex_colors) == 2 and 3 <= vertex_colors.shape[1] <= 4), \
            f"Expected colors array of shape (N,3) or (N,4) got shape {vertex_colors.shape}"
        assert vertex_colors.dtype in [np.float32, np.float64], \
            "Colors should be stored as floating point numbers (np.float32 or np.float64)"
        assert np.all(vertex_colors >= 0) and np.all(vertex_colors <= 1), "Colors should be in range [0.0, 1.0]"
        has_alpha = vertex_colors.shape[1] == 4
        if not has_alpha:
            vertex_colors = np.hstack([vertex_colors, np.ones((vertex_colors.shape[0], 1), dtype=vertex_colors.dtype)])
        self._vertex_colors = vertex_colors.copy()
        self._metadata = ColorsMetadata(
            type=self.__class__,
            has_alpha=has_alpha,
            color=None,
            texture=None
        )

    @property
    def vertex_colors(self) -> np.ndarray:
        """Get current colors

        Returns:
            np.ndarray: current vertex colors
        """
        return self._vertex_colors


class UniformColors(Colors):
    """A container which stores a single uniform color for the whole object
    """

    def __init__(self, uniform_color: Union[Vector3d, Vector4d]):
        """Create the uniform color container

        Args:
            uniform_color (Vector3d): a color in RGB format (to change alpha, use 'alpha' material property instead)
        """
        super().__init__()
        uniform_color = np.array(uniform_color)
        assert len(uniform_color) in (3, 4), "Color should be in RGB or RGBA format"
        assert uniform_color.max() <= 1. and uniform_color.min() >= 0., "Color values should be in [0,1] range"
        self._color = uniform_color
        self._metadata = ColorsMetadata(
            type=self.__class__,
            has_alpha=self._color.shape[0] == 4,
            color=self._color,
            texture=None
        )

    @property
    def color(self) -> np.ndarray:
        """Get current color

        Returns:
            np.ndarray: current color
        """
        return self._color
