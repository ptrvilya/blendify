import math
from collections import defaultdict

import bpy
import numpy as np
from scipy.spatial.transform import Rotation


def _move_objects(from_col, to_col, linked, dupe_lut):
    for o in from_col.objects:
        dupe = o.copy()
        if not linked and o.data:
            dupe.data = dupe.data.copy()
        to_col.objects.link(dupe)
        from_col.objects.unlink(o)

        dupe_lut[o] = dupe


def move_collection(parent, collection, linked=False):
    # from https://blender.stackexchange.com/questions/157828/how-to-duplicate-a-certain-collection-using-python
    dupe_lookuptable = defaultdict(lambda: None)

    def _move_collection(parent, collection, linked=False):
        cc = bpy.data.collections.new(collection.name)
        _move_objects(collection, cc, linked, dupe_lookuptable)

        for c in collection.children:
            _move_collection(cc, c, linked)

        parent.children.link(cc)
        for c in collection.children:
            bpy.data.collections.remove(c, do_unlink=True)

    _move_collection(parent, collection, linked)

    for o, dupe in tuple(dupe_lookuptable.items()):
        parent = dupe_lookuptable[o.parent]
        if parent:
            dupe.parent = parent


def parse_camera_from_blendfile(obj: bpy.types.Object, resolution: np.ndarray):
    """Parse camera parameters from blender object.
    Args:
        obj (bpy.types.Object): Blender object with camera data
        resolution (np.ndarray): array of [resolution_x, resolution_y]

    Returns:
        camera_type (str): ORTHO, PRESP or NONE
        camera_dict (dict): dictionary with camera parameters
    """
    camera_dict = dict()
    camera_dict["tag"] = obj.name
    camera_dict["resolution"] = resolution

    # position
    camera_dict["translation"] = np.array(obj.location)
    if obj.rotation_mode == "QUATERNION":
        camera_dict["quaternion"] = np.array(obj.rotation_quaternion)
    elif obj.rotation_mode == "AXIS_ANGLE":
        rotvec = np.array(obj.rotation_axis_angle)
        angle, axis = rotvec[0], rotvec[1:]
        rotvec = (axis / np.linalg.norm(axis)) * angle

        rot = Rotation.from_rotvec(rotvec)
        camera_dict["quaternion"] = np.roll(rot.as_quat(), 1)
    else:
        # euler angles
        rot_data = obj.rotation_euler
        mode = rot_data.order
        angles = np.array(rot_data[:])

        rot = Rotation.from_euler(mode.lower(), angles, degrees=False)
        camera_dict["quaternion"] = np.roll(rot.as_quat(), 1)

    # camera parameters
    if obj.data.type == "ORTHO":
        # scale
        camera_dict["ortho_scale"] = obj.data.ortho_scale

        # near / far
        camera_dict["near"] = obj.data.clip_start
        camera_dict["far"] = obj.data.clip_end
    elif obj.data.type == "PERSP":
        # sensor params
        fov_x, fov_y = None, None
        sensor_fit = obj.data.sensor_fit

        # determine sensor fit
        if sensor_fit == "AUTO":
            sensor_fit = "HORIZONTAL" if resolution[0] >= resolution[1] else "VERTICAL"

        # determine fov
        if sensor_fit == "HORIZONTAL":
            if obj.data.lens_unit == "MILLETERS":
                fov_x = 2 * math.atan(0.5 * obj.data.sensor_width / obj.data.lens)
            else:
                fov_x = obj.data.angle_x
        else:  # VERTICAL
            if obj.data.lens_unit == "MILLETERS":
                fov_y = 2 * math.atan(0.5 * obj.data.sensor_height / obj.data.lens)
            else:
                fov_y = obj.data.angle_y
        camera_dict["fov_x"] = fov_x
        camera_dict["fov_y"] = fov_y

        # center
        ideal_center = resolution / 2.
        center_offset = np.array([obj.data.shift_x, obj.data.shift_y])
        camera_dict["center"] = ideal_center + center_offset

        # near / far
        camera_dict["near"] = obj.data.clip_start
        camera_dict["far"] = obj.data.clip_end

    return obj.data.type, camera_dict
