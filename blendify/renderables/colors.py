from abc import ABC, abstractmethod
from typing import NamedTuple, Optional

import bpy
import numpy as np

from ..internal.texture import _copy_values_to_image
from ..internal.types import Vector3d


class ColorsMetadata(NamedTuple):
    type: type
    color: Optional[Vector3d]
    has_alpha: bool
    texture: Optional[bpy.types.Image]


class Colors(ABC):
    """An abstract container template for storing the object coloring information
    """
    @abstractmethod
    def __init__(self):
        self._metadata: Optional[ColorsMetadata] = None

    @property
    def metadata(self) -> ColorsMetadata:
        return self._metadata


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
        assert vertex_colors.dtype in [np.float32, np.float64],\
            "Colors shoud be stored as floating point numbers (np.float32 or np.float64)"
        assert np.all(vertex_colors >= 0) and np.all(vertex_colors <= 1), "Colors should be in range [0.0, 1.0]"
        self._vertex_colors = vertex_colors
        self._metadata = ColorsMetadata(
            type=self.__class__,
            has_alpha=self._vertex_colors.shape[1] == 4,
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
    def __init__(self, uniform_color: Vector3d):
        """Create the uniform color container

        Args:
            uniform_color (Vector3d): a color in RGB format (to change alpha, use 'alpha' material property instead)
        """
        super().__init__()
        uniform_color = np.array(uniform_color)
        assert len(uniform_color) == 3, "Color should be in RGB format"
        assert uniform_color.max() <= 1. and uniform_color.min() >= 0., "Color values should be in [0,1] range"
        self._color = uniform_color
        self._metadata = ColorsMetadata(
            type=self.__class__,
            has_alpha=False,
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


class UVMap(ABC):
    """An abstract container template for storing a UV coordinate map
    """
    @abstractmethod
    def __init__(self, data: np.ndarray):
        self._data = data

    @property
    def data(self) -> np.ndarray:
        """Get the stored UV map data

        Returns:
            np.ndarray: UV map data
        """
        return self._data


class VertexUV(UVMap):
    """A container which stores a UV coordinate for every vertex
    In the form of (N,2) array (N vertices, 2 UV coordinates for each)
    """
    def __init__(self, data: np.ndarray):
        super().__init__(data)


class FacesUV(UVMap):
    """A container which stores a UV coordinate for every vertex in every triangle face
    In the form of (M,3,2) array (M faces, 3 vertices in each face, 2 UV coordinates for each vertex in triangle)
    """
    def __init__(self, data: np.ndarray):
        super().__init__(data)


class UVColors(Colors):
    """An abstract container for storing color information bound to UV coordinate space
    """
    @abstractmethod
    def __init__(self, uv_map: UVMap):
        super().__init__()
        self._uv_map = uv_map

    @property
    def uv_map(self) -> UVMap:
        """Get the stored UV map

        Returns:
            UVMap: stored UV map
        """
        return self._uv_map


class TextureColors(UVColors):
    """A container which stores texture in form of pixels array and the corresponding UV mapping
    """
    def __init__(self, texture: np.ndarray, uv_map: UVMap):
        """Create the texture container and initialize a Blender texture with the pixels data

        Args:
            texture (np.ndarray): pixels data
            uv_map (UVMap): corresponding UV map
        """
        super().__init__(uv_map)
        if texture.dtype == np.uint8:
            texture = texture.astype(np.float32)/255.
        blender_image = bpy.data.images.new(name="tex_image", width=texture.shape[1],
                                            height=texture.shape[0])
        _copy_values_to_image(texture.reshape(-1, 3), blender_image.name)
        self._texture = blender_image
        self._metadata = ColorsMetadata(
            type=self.__class__,
            has_alpha=False,
            color=None,
            texture= self._texture
        )

    @property
    def blender_texture(self) -> bpy.types.Image:
        """Get the current Blender texture created from the pixels array

        Returns:
            bpy.types.Image: current Blender texture
        """
        return self._texture


class FileTextureColors(UVColors):
    """A container which stores path to the texture file and the corresponding UV mapping
    """
    def __init__(self, texture_path: str, uv_map: UVMap):
        """Create the texture container and load the texture from the path as a Blender texture

        Args:
            texture_path (str): path to the texture
            uv_map: corresponding UV map
        """
        super().__init__(uv_map)
        self._texture = bpy.data.images.load(texture_path)
        self._metadata = ColorsMetadata(
            type=self.__class__,
            has_alpha=False,
            color=None,
            texture=self._texture
        )

    @property
    def blender_texture(self) -> bpy.types.Image:
        """Get the current Blender texture created from the pixels array

        Returns:
            bpy.types.Image: current Blender texture
        """
        return self._texture
