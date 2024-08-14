import numpy as np

from .base import Camera
from ..internal.types import Vector2d


class PerspectiveCamera(Camera):
    def __init__(
        self,
        focal_dist: float = None,
        fov_x: float = None,
        fov_y: float = None,
        center: Vector2d = None,
        **kwargs
    ):
        """Creates Perspective Camera object in Blender. One of focal_dist, fov_x or fov_y is required to
        set the camera parameters

        Args:
            focal_dist (float, optional): Perspective Camera focal distance in millimeters (default: None)
            fov_x (float, optional): Camera lens horizontal field of view (default: None)
            fov_y (float, optional): Camera lens vertical field of view (default: None)
            center (Vector2d, optional): (x, y), horizontal and vertical shifts of the Camera (default: None)
            resolution (Vector2di): (w, h), the resolution of the resulting image
            near (float, optional): Camera near clipping distance (default: 0.1)
            far (float, optional): Camera far clipping distance (default: 100)
            rotation_mode (str): type of rotation representation.
                Can be one of the following:
                - "quaternionWXYZ" - WXYZ quaternion
                - "quaternionXYZW" - XYZW quaternion
                - "rotvec" - axis-angle representation of rotation
                - "rotmat" - 3x3 rotation matrix
                - "euler<mode>" - Euler angles with the specified order of rotation, e.g. XYZ, xyz, ZXZ, etc. Refer to scipy.spatial.transform.Rotation.from_euler for details.
                - "look_at" - look at rotation, the rotation is defined by the point to look at and, optional, the rotation around the forward direction vector (a single float value in tuple or list)
            rotation (RotationParams): rotation parameters according to the rotation_mode
                - for "quaternionWXYZ" and "quaternionXYZW" - Vec4d
                - for "rotvec" - Vec3d
                - for "rotmat" - Mat3x3
                - for "euler<mode>" - Vec3d
                - for "look_at" - Vec3d, Positionable or Tuple[Vec3d/Positionable, float], where float is the rotation around the forward direction vector in degrees
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
        # Blender's camera shift is relative and bounded by [-2, 2]
        center_offset_relative = np.array([camera.data.shift_x, camera.data.shift_y])
        real_center = ideal_center + center_offset_relative * self.resolution
        return real_center

    @center.setter
    def center(self, real_center: Vector2d):
        assert np.all(np.array(real_center) >= -2) and np.all(np.array(real_center) <= 2), \
            ("Blender's camera center is set as a fraction of resolution and "
             "should be in [-2, 2], got {}").format(real_center)
        camera = self.blender_camera
        real_center = np.array(real_center)
        ideal_center = self.resolution / 2.
        center_offset_relative = real_center - ideal_center / self.resolution
        camera.data.shift_x = center_offset_relative[0]
        camera.data.shift_y = center_offset_relative[1]

    def distance2depth(self, distmap: np.ndarray) -> np.ndarray:
        """Convert map of camera ray lengths (distmap) to map of distances to image plane (depthmap)

        Args:
            distmap (np.ndarray): Distance map

        Returns:
            np.ndarray: Depth map
        """
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
        """Creates Orthographic Camera object in Blender

        Args:
            ortho_scale (float, optional): Orthographic Camera scale (similar to zoom) (default: 1.0)
            resolution (Vector2di): (w, h), the resolution of the resulting image
            near (float, optional): Camera near clipping distance (default: 0.1)
            far (float, optional): Camera far clipping distance (default: 100)
            rotation_mode (str): type of rotation representation.
                Can be one of the following:
                - "quaternionWXYZ" - WXYZ quaternion
                - "quaternionXYZW" - XYZW quaternion
                - "rotvec" - axis-angle representation of rotation
                - "rotmat" - 3x3 rotation matrix
                - "euler<mode>" - Euler angles with the specified order of rotation, e.g. XYZ, xyz, ZXZ, etc. Refer to scipy.spatial.transform.Rotation.from_euler for details.
                - "look_at" - look at rotation, the rotation is defined by the point to look at and, optional, the rotation around the forward direction vector (a single float value in tuple or list)
            rotation (RotationParams): rotation parameters according to the rotation_mode
                - for "quaternionWXYZ" and "quaternionXYZW" - Vec4d
                - for "rotvec" - Vec3d
                - for "rotmat" - Mat3x3
                - for "euler<mode>" - Vec3d
                - for "look_at" - Vec3d, Positionable or Tuple[Vec3d/Positionable, float], where float is the rotation around the forward direction vector in degrees
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

    def distance2depth(self, distmap: np.ndarray) -> np.ndarray:
        """Convert map of camera ray lengths (distmap) to map of distances to image plane (depthmap)

        Args:
            distmap (np.ndarray): Distance map

        Returns:
            np.ndarray: Depth map
        """
        # In orthogonal camera rays are orthogonal to the image plane => distmap = depthmap
        return distmap
