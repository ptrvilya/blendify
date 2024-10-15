from abc import ABC, abstractmethod

import bpy
import numpy as np
from scipy.spatial.transform import Rotation

from ..internal.types import BlenderGroup, Vector3d, Vector4d, RotationParams


class Positionable(ABC):
    """Base class for all classes that wrap Blender objects with location in space (Camera, Light, Renderable)
    """

    @abstractmethod
    def __init__(
            self,
            tag: str,
            blender_object: BlenderGroup,
            rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None,
            translation: Vector3d = (0, 0, 0)
    ):
        """Sets initial position of the Blender object and stores it. Called from child classes

        Args:
            tag (str): name of the object in Blender that was created in child class
            blender_object (bpy.types.Object): instance of Blender Object that is wrapped by the child class
            quaternion (RotationParams, optional): rotation applied to the Blender object (default: None (identity))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
        """
        self._blender_object = blender_object
        self._tag = tag
        self._quaternion = np.array((1, 0, 0, 0), dtype=np.float64)
        self._translation = np.array((0, 0, 0), dtype=np.float64)
        self.set_position(rotation_mode, rotation, translation)

    @property
    def tag(self):
        return self._tag

    def _rotation_params_to_quat(self, rotation_mode: str = "quaternionWXYZ", rotation: RotationParams = None):
        """
        Converts rotation parameters to quaternion representation
        Args:
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
        Returns:
            np.ndarray: quaternion representation of the rotation
        """
        if rotation is None:
            return None
        if rotation_mode.startswith("quaternion"):
            roll_quat = rotation_mode.lower() == "quaternionxyzw"
            result = np.roll(rotation, 1) if roll_quat else np.array(rotation)
        elif rotation_mode == "rotvec":
            result = np.roll(Rotation.from_rotvec(rotation).as_quat(), 1)
        elif rotation_mode == "rotmat":
            result = np.roll(Rotation.from_matrix(rotation).as_quat(), 1)
        elif rotation_mode.startswith("euler"):
            euler_order = rotation_mode[len("euler"):]
            result = np.roll(Rotation.from_euler(euler_order, rotation, degrees=True).as_quat(), 1)
        elif rotation_mode in ["look_at", "lookat"]:
            look_at_rotation_deg = 0.
            if isinstance(rotation, (tuple, list)) and len(rotation) == 2:
                rotation, look_at_rotation_deg = rotation
            if isinstance(rotation, Positionable):
                look_at = rotation.translation
            else:
                look_at = np.array(rotation)
            translation = np.array(self.translation)
            forward_vec =  translation - look_at
            if (forward_vec_norm:=np.linalg.norm(forward_vec)) < 1e-10:
                result = np.array([1, 0, 0, 0])
            else:
                forward_vec /= forward_vec_norm
                up_vec = np.array([0, 0, 1] if (1 - np.abs(forward_vec[2])) > 1e-10 else [0, 1, 0])
                right_vec = np.cross(up_vec, forward_vec)
                right_vec /= np.linalg.norm(right_vec)
                up_vec = np.cross(forward_vec, right_vec)
                up_vec /= np.linalg.norm(up_vec)
                rotmat = np.stack([right_vec, up_vec, forward_vec], axis=1)
                rot = Rotation.from_matrix(rotmat)
                if np.abs(look_at_rotation_deg) > 1e-10:
                    rot = rot * Rotation.from_euler('Z', look_at_rotation_deg, degrees=True)
                result = np.roll(rot.as_quat(), 1)
        else:
            raise ValueError(f"Unknown rotation mode: {rotation_mode}")
        return result.astype(np.float64)

    def set_position(self, rotation_mode: str = "quaternionWXYZ", rotation: RotationParams = None, translation: Vector3d = None):
        """Sets the position of the object in the scene
        
        Args:
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
            translation (Vector3d): translation vector
        """

        if translation is not None:
            self._translation = np.array(translation, dtype=np.float64)
        if (quaternion := self._rotation_params_to_quat(rotation_mode, rotation)) is not None:
            self._quaternion = quaternion
        self._update_position()

    @property
    def quaternion(self):
        return self._quaternion

    @quaternion.setter
    def quaternion(self, val: Vector4d):
        self._quaternion = np.array(val)
        self._update_position()

    @property
    def translation(self):
        return self._translation

    @translation.setter
    def translation(self, val: Vector3d):
        self._translation = np.array(val)
        self._update_position()

    def _update_position(self):
        self._set_blender_object_position(self._blender_object)

    def _set_blender_object_position(self, blender_object: BlenderGroup):
        def set_position(obj):
            obj.rotation_mode = 'QUATERNION'
            obj.rotation_quaternion = self.quaternion.tolist()
            obj.location = self.translation.tolist()

        if isinstance(blender_object, bpy.types.Collection):
            for obj in blender_object.all_objects.values():
                set_position(obj)
        else:
            set_position(blender_object)

    def _blender_remove_object(self):
        """Removes the object from Blender scene"""
        bpy.ops.object.select_all(action='DESELECT')
        is_collection = isinstance(self._blender_object, bpy.types.Collection)
        if is_collection:
            for obj in self._blender_object.all_objects.values():
                obj.select_set(True)
        else:
            bpy.context.view_layer.objects.active = self._blender_object
            bpy.ops.object.mode_set(mode='OBJECT')
            self._blender_object.select_set(True)
        bpy.ops.object.delete()
        if is_collection:
            bpy.data.collections.remove(self._blender_object)
        self._blender_object = None
