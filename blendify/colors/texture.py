from abc import ABC, abstractmethod

import bpy
import numpy as np

from .base import Colors, ColorsMetadata
from ..internal.texture import _copy_values_to_image


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
        assert texture.ndim == 3 and texture.shape[2] in (3, 4), "Texture must be a 3D array of shape (H, W, 3) or (H, W, 4)"
        super().__init__(uv_map)
        if texture.dtype == np.uint8:
            texture = texture.astype(np.float32)/255.
        blender_image = bpy.data.images.new(name="tex_image", width=texture.shape[1],
                                            height=texture.shape[0])
        last_dim = texture.shape[2]
        # Flip the data vertically before copying
        texture = texture[::-1]
        _copy_values_to_image(texture.reshape(-1, last_dim), blender_image.name)
        blender_image.pack()
        self._texture = blender_image
        self._metadata = ColorsMetadata(
            type=self.__class__,
            has_alpha=last_dim == 4,
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
            has_alpha=True,
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
