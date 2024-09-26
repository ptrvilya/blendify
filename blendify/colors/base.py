from abc import ABC, abstractmethod
from typing import NamedTuple, Optional, Union, Sequence

import bpy

from ..internal.types import Vector3d


class ColorsMetadata(NamedTuple):
    type: type
    color: Optional[Vector3d]
    has_alpha: bool
    texture: Optional[bpy.types.Image]

    def __del__(self):
        if self.texture is not None:
            if not self.texture.users:
                bpy.data.images.remove(self.texture)


class Colors(ABC):
    """An abstract container template for storing the object coloring information
    """

    @abstractmethod
    def __init__(self):
        self._metadata: Optional[ColorsMetadata] = None

    @property
    def metadata(self) -> ColorsMetadata:
        return self._metadata


ColorsList = Sequence[Colors]
