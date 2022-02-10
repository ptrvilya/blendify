from abc import abstractmethod

import bpy
import numpy as np
from scipy.spatial import transform

from .internal.positionable import Positionable
from .internal.types import Vector2d, Vector2di, Vector3d, Vector4d


class Camera(Positionable):
    """
    Base class for PerspectiveCamera and OrthographicCamera, implementing shared functionality.
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
        """
        Implements the creation of camera in Blender. Called by child classes.
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
        """
        Convert map of camera ray lengths (distmap) to map of distances to image plane (depthmap)
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

    def get_camera_ray(self):
        # TODO substitute for array of rays for each pixel for perspective camera?
        # Default blender camera: up is aligned with +y, ray: (0,0,-1)
        camera_ray = np.array([0, 0, -1], dtype=np.float32)

        # scipy quat is [x, y, z, w], while ours is [w, x, y, z]
        rotation = transform.Rotation.from_quat(np.roll(self.quaternion, -1))
        camera_ray = rotation.apply(camera_ray)
        return camera_ray

    def _update_position(self):
        # Bad hack to avoid circular import
        from . import get_scene
        get_scene().renderables.update_camera(self)
        super()._update_position()


class PerspectiveCamera(Camera):
    def __init__(
        self,
        focal_dist: float = None,
        fov_x: float = None,
        fov_y: float = None,
        center: Vector2d = None,
        **kwargs
    ):
        """
        Creates Perspective Camera object in Blender. One of focal_dist, fov_x or fov_y is required to
        set the camera parameters
        Args:
            resolution (Vector2di): (w, h), the resolution of the resulting image
            focal_dist (float, optional): Perspective Camera focal distance in millimeters (default: None)
            fov_x (float, optional): Camera lens horizontal field of view (default: None)
            fov_y (float, optional): Camera lens vertical field of view (default: None)
            center (Vector2d, optional): (x, y), horizontal and vertical shifts of the Camera (default: None)
            near (float, optional): Camera near clipping distance (default: 0.1)
            far (float, optional): Camera far clipping distance (default: 100)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        super().__init__(**kwargs)
        assert not(focal_dist is None and fov_x is None and fov_y is None), \
            "One of focal_dist, fov_x or fov_y is required"
        camera_object = self.blender_camera
        camera_object.data.type = 'PERSP'
        # camera.data.lens_unit = "FOV"
        if focal_dist is not None:
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
    def center(self, real_center: Vector2d):
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
    def __init__(
        self,
        ortho_scale: float = 1.,
        **kwargs
    ):
        """
        Creates Orthographic Camera object in Blender.
        Args:
            resolution (Vector2di): (w, h), the resolution of the resulting image
            ortho_scale (float, optional): Orthographic Camera scale (similar to zoom) (default: 1.0)
            near (float, optional): Camera near clipping distance (default: 0.1)
            far (float, optional): Camera far clipping distance (default: 100)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        super().__init__(**kwargs)
        camera_object = self.blender_camera
        camera_object.data.type = 'ORTHO'
        self.ortho_scale = ortho_scale

    @property
    def ortho_scale(self) -> float:
        return self.blender_camera.data.ortho_scale

    @ortho_scale.setter
    def ortho_scale(self, val: float):
        self.blender_camera.data.ortho_scale = val

    def distance2depth(self, distmap):
        # In orthogonal camera rays are orthogonal to the image plane => distmap = depthmap
        return distmap
