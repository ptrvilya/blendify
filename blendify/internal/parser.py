import math
from collections import defaultdict

import bpy
import numpy as np
from scipy.spatial.transform import Rotation


def move_collection(parent, collection):
    # from https://blender.stackexchange.com/questions/157828/how-to-duplicate-a-certain-collection-using-python
    def _move_collection(parent, collection):
        # re-link objects
        for o in collection.objects:
            collection.objects.unlink(o)
            parent.objects.link(o)

        for c in collection.children:
            # Create child and link it
            cc = bpy.data.collections.new(c.name)
            parent.children.link(cc)
            # Fix naming: blender appends .001, .002, etc. to new names
            orig_name = c.name
            created_name = cc.name
            c.name = created_name
            cc.name = orig_name
            # Recursively move everything that is inside
            _move_collection(cc, c)

        for c in collection.children:
            bpy.data.collections.remove(c, do_unlink=True)

    _move_collection(parent, collection)


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
        camera_dict["rotation"] = np.array(obj.rotation_quaternion)
    elif obj.rotation_mode == "AXIS_ANGLE":
        rotvec = np.array(obj.rotation_axis_angle)
        angle, axis = rotvec[0], rotvec[1:]
        rotvec = (axis / np.linalg.norm(axis)) * angle

        rot = Rotation.from_rotvec(rotvec)
        camera_dict["rotation"] = np.roll(rot.as_quat(), 1)
    else:
        # euler angles
        rot_data = obj.rotation_euler
        mode = rot_data.order
        angles = np.array(rot_data[:])

        rot = Rotation.from_euler(mode.lower(), angles, degrees=False)
        camera_dict["rotation"] = np.roll(rot.as_quat(), 1)

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
        camera_dict["center"] = ideal_center / resolution - center_offset

        # near / far
        camera_dict["near"] = obj.data.clip_start
        camera_dict["far"] = obj.data.clip_end

    return obj.data.type, camera_dict

def parse_light_from_blendfile(obj: bpy.types.Object):
    # Parse common parameters
    translation, quaternion, scale = obj.matrix_world.decompose()
    # "scale", "multiple_importance", "shadow_caustics" are not supported
    light_dict = {
        "strength": obj.data.energy,
        "color": np.array(obj.data.color),
        "cast_shadows": obj.data.cycles.cast_shadow,
        "rotation": quaternion,
        "translation": translation,
        "tag": obj.name
    }

    # Parse type specific parameters
    light_type = obj.data.type
    if light_type == "POINT":
        light_dict["shadow_soft_size"] = obj.data.shadow_soft_size
    elif light_type == "SUN":
        light_dict["angular_diameter"] = obj.data.angle
    elif light_type == "SPOT":
        light_dict["spot_size"] = obj.data.spot_size
        light_dict["spot_blend"] = obj.data.spot_blend
        light_dict["shadow_soft_size"] = obj.data.shadow_soft_size
    elif light_type == "AREA":
        light_dict["shape"] = obj.data.shape.lower()
        if light_dict["shape"] in ["RECTANGLE", "ELLIPSE"]:
            light_dict["size"] = np.array([obj.data.size, obj.data.size_y], dtype=np.float32)
        else:
            light_dict["size"] = obj.data.size

    return light_type, light_dict
