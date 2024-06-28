from typing import Union, Tuple

import bpy
import numpy as np

BlenderGroup = Union[bpy.types.Collection, bpy.types.Object]
Vector2d = Union[np.ndarray, Tuple[float, float]]
Vector2di = Union[np.ndarray, Tuple[int, int]]
Vector3d = Union[np.ndarray, Tuple[float, float, float]]
Vector3di = Union[np.ndarray, Tuple[int, int, int]]
Vector4d = Union[np.ndarray, Tuple[float, float, float, float]]
Mat3x3 = Union[np.ndarray, Tuple[Tuple[float, float, float], Tuple[float, float, float], Tuple[float, float, float]]]
RotationParams = Union[Vector4d, Vector3d, Mat3x3, "Positionable", Tuple[Vector3d, float], Tuple["Positionable", float]]