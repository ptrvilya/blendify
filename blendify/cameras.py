import numpy as np
import bpy
import bpy_types
from abc import ABC, abstractmethod
from typing import Union, Tuple, List, Sequence
from .internal.positionable import Positionable
from .internal.types import Vector2df, Vector2di, Vector3d, Vector4d


class Camera(Positionable):
    def _blender_create_camera(self, tag):
        bpy.ops.object.camera_add()
        camera_object = bpy.data.objects['Camera']
        camera_object.name = tag
        return camera_object

    @abstractmethod
    def __init__(self, resolution: Vector2di, quaternion: Vector4d = (1, 0, 0, 0),
                 translation: Vector3d = (0, 0, 0), tag: str = 'camera'):
        camera_object = self._blender_create_camera(tag)
        super().__init__(tag, camera_object)
        camera_object.data.sensor_fit = 'HORIZONTAL'
        camera_object.data.sensor_width = resolution[0]
        camera_object.data.sensor_height = resolution[1]
        self._resolution = np.array(resolution)

        self.set_position(quaternion=quaternion, translation=translation)

    @property
    def resolution(self) -> np.ndarray:
        return self._resolution

    @property
    def blender_camera(self) -> bpy_types.Object:
        return self._blender_object

    @abstractmethod
    def distance2depth(self, distmap: np.ndarray) -> np.ndarray:
        """
        Convert map of camera ray lengths (distmap) to map of distances to image plane (depthmap)
        Args:
            distmap (np.ndarray): Distance map

        Returns:
            np.ndarray: Depth map
        """
        pass


class PerspectiveCamera(Camera):
    def __init__(self, resolution: Vector2di, focal_dist: float,
                 fov_x: float = None, fov_y: float = None,
                 quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0),
                 center: Vector2df = None, tag: str = 'camera'):
        super().__init__(resolution, quaternion, translation, tag)
        camera_object = self.blender_camera
        camera_object.data.type = 'PERSP'
        # camera.data.lens_unit = "FOV"
        self.focal_dist = focal_dist
        if center is not None:
            self.center = center
        if fov_x is not None:
            self.fov_x = fov_x
        if fov_y is not None:
            self.fov_y = fov_y

    @property
    def focal_dist(self):
        return self.blender_camera.data.lens

    @focal_dist.setter
    def focal_dist(self, focal: float):
        camera = self.blender_camera
        self._focal_dist = focal
        camera.data.lens = focal

    @property
    def fov_x(self):
        return self.blender_camera.data.angle_x

    @fov_x.setter
    def fov_x(self, val: float):
        self.blender_camera.data.angle_x = val

    @property
    def fov_y(self):
        return self.blender_camera.data.angle_y

    @fov_y.setter
    def fov_y(self, val: float):
        self.blender_camera.data.angle_y = val

    @property
    def center(self) -> np.ndarray:
        camera = self.blender_camera
        ideal_center = self.resolution / 2.
        center_offset = np.array([camera.data.shift_x, camera.data.shift_y])
        real_center = ideal_center + center_offset
        return real_center

    @center.setter
    def center(self, real_center: Vector2df):
        camera = self.blender_camera
        real_center = np.array(real_center)
        ideal_center = self.resolution / 2.
        center_offset = real_center - ideal_center
        camera.data.shift_x = center_offset[0]
        camera.data.shift_y = center_offset[1]

    def distance2depth(self, distmap):
        img_width, img_height = self.resolution
        cx, cy = self.center
        offsets_x = np.arange(img_width) - cx
        offsets_y = np.arange(img_height) - cy
        grid_offsets_x, grid_offsets_y = np.meshgrid(offsets_x, offsets_y)
        depthmap = np.sqrt(distmap ** 2 / ((grid_offsets_x ** 2 + grid_offsets_y ** 2) / (self.focal_dist ** 2) + 1))
        return depthmap



class OrthographicCamera(Camera):
    def __init__(self, resolution: Vector2di, ortho_scale: float = 1.,
                 quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0),
                 far: float = 1., near: float = 0.1, tag: str = 'camera'):
        super().__init__(resolution, quaternion, translation, tag)
        camera_object = self.blender_camera
        camera_object.data.type = 'ORTHO'
        self.ortho_scale = ortho_scale
        self.near = near
        self.far = far

    @property
    def ortho_scale(self) -> float:
        return self.blender_camera.data.ortho_scale

    @ortho_scale.setter
    def ortho_scale(self, val: float):
        self.blender_camera.data.ortho_scale = val

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

    def distance2depth(self, distmap):
        # In orthogonal camera rays are orthogonal to the image plane => distmap = depthmap
        return distmap
