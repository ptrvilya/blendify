import numpy as np
import bpy
import bpy_types
from typing import Sequence, Union, Tuple, List

BlenderGroup = Union[bpy.types.Collection, bpy_types.Object]
Vector2d = Union[np.ndarray, Tuple[float,float,float]]
Vector3d = Union[np.ndarray, Tuple[float,float,float]]