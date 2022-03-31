from abc import abstractmethod

import bpy
import numpy as np
from scipy.spatial import transform

from ..internal.positionable import Positionable
from ..internal.types import Vector2di


class Camera(Positionable):
    """Base class for PerspectiveCamera and OrthographicCamera, implementing shared functionality
    """
    @abstractmethod
    def __init__(
        self,
        resolution: Vector2di,
        near: float = 0.1,
        far: float = 100,
        tag: str = 'camera',
        **kwargs
    ):
        """Implements the creation of camera in Blender. Called by child classes

        Args:
            resolution (Vector2di): (w, h), the resolution of the resulting image
            near (float, optional): Camera near clipping distance (default: 0.1)
            far (float, optional): Camera far clipping distance (default: 100)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        camera_object = self._blender_create_camera(tag)
        super().__init__(**kwargs, tag=tag, blender_object=camera_object)
        camera_object.data.sensor_fit = 'HORIZONTAL'
        camera_object.data.sensor_width = resolution[0]
        camera_object.data.sensor_height = resolution[1]
        self.near = near
        self.far = far

        self._resolution = np.array(resolution)

    def _blender_create_camera(self, tag):
        bpy.ops.object.camera_add()
        camera_object = bpy.data.objects['Camera']
        camera_object.name = tag
        return camera_object

    @property
    def resolution(self) -> np.ndarray:
        return self._resolution

    @property
    def blender_camera(self) -> bpy.types.Object:
        return self._blender_object

    @abstractmethod
    def distance2depth(self, distmap: np.ndarray) -> np.ndarray:
        """Convert map of camera ray lengths (distmap) to map of distances to image plane (depthmap)

        Args:
            distmap (np.ndarray): Distance map

        Returns:
            np.ndarray: Depth map
        """
        pass

    @property
    def near(self) -> float:
        return self.blender_camera.data.clip_start

    @near.setter
    def near(self, val: float):
        self.blender_camera.data.clip_start = val

    @property
    def far(self) -> float:
        return self.blender_camera.data.clip_end

    @far.setter
    def far(self, val: float):
        self.blender_camera.data.clip_end = val

    def get_camera_viewdir(self):
        # Default blender camera: up is aligned with +y, ray: (0,0,-1)
        camera_ray = np.array([0, 0, -1], dtype=np.float32)

        # scipy quat is [x, y, z, w], while ours is [w, x, y, z]
        rotation = transform.Rotation.from_quat(np.roll(self.quaternion, -1))
        camera_ray = rotation.apply(camera_ray)
        return camera_ray

    def _update_position(self):
        super()._update_position()
