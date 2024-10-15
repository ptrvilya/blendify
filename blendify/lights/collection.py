from typing import Dict, Iterable, Union

import bpy
import numpy as np

from .base import Light
from .common import PointLight, DirectionalLight, SpotLight
from .area import AreaLight, SquareAreaLight, CircleAreaLight, RectangleAreaLight, EllipseAreaLight
from ..internal import Singleton
from ..internal.types import Vector2d, Vector3d, RotationParams


class LightsCollection(metaclass=Singleton):
    def __init__(self):
        self._lights: Dict[str, Light] = dict()
        self._background_light_nodes = None

    def remove_background_light(self):
        """
        Remove background light from the scene. Also removes ShaderNodeBackground if
        it was added via scene.attach_blend.

        Returns:
            None
        """
        world = bpy.context.scene.world
        world.use_nodes = True
        world_tree = world.node_tree

        if self._background_light_nodes is not None:
            for node_name in self._background_light_nodes:
                node = world_tree.nodes.get(node_name)
                world_tree.nodes.remove(node)
            self._background_light_nodes = None
        else:
            for node in world_tree.nodes:
                if node.type == 'BACKGROUND':
                    world_tree.nodes.remove(node)

    def set_background_light(self, strength: float = 1.0, color: Vector3d = (1.0, 1.0, 1.0)):
        """
        Set background light in a scene. Can be used to create ambient lightning in a scene.

        Returns:
            None
        """
        color = np.array(color)
        assert color.dtype in [np.float32, np.float64], \
            "Color should be stored as floating point numbers (np.float32 or np.float64)"
        world = bpy.context.scene.world
        world.use_nodes = True
        world_tree = world.node_tree

        self.remove_background_light()
        # Create light node and output node
        bg_node = world_tree.nodes.new(type='ShaderNodeBackground')
        for node in world_tree.nodes:
            if node.type == 'OUTPUT_WORLD':
                output_node = node
                break
        else:
            output_node = world_tree.nodes.new(type='ShaderNodeOutputWorld')

        # Set light color
        if len(color == 3):
            color = (*color, 1.0)
        bg_node.inputs['Color'].default_value = color

        # Link light to output and set strength
        world_tree.links.new(bg_node.outputs['Background'], output_node.inputs['Surface'])
        bg_node.inputs['Strength'].default_value = strength

        # Save created nodes to remove them later
        self._background_light_nodes = [bg_node.name, output_node.name]

    def add_point(
            self,
            strength: float = 100,
            shadow_soft_size: float = 0.25,
            color: Vector3d = (1.0, 1.0, 1.0),
            cast_shadows=True,
            rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None,
            translation: Vector3d = (0, 0, 0),
            tag=None
    ) -> PointLight:
        """Add PointLight light source to the scene

        Args:
            strength (float, optional): strength of the light source emitted over the entire area of the light
                in all directions (default: 100)
            shadow_soft_size (float, optional): light size for ray shadow sampling (Raytraced shadows)
                in [0, inf] (default: 0.25)
            color (Vector3d, optional): color of the light source (default: (1.0, 1.0, 1.0))
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
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
            tag (str, optional): name of the created collection in Blender to represent the point cloud.
                If None is passed the tag is automatically generated (default: None)

        Returns:
            PointLight: created and added to the scene object
        """
        tag = self._process_tag(tag, "Point")
        light = PointLight(
            color=color, strength=strength, shadow_soft_size=shadow_soft_size, cast_shadows=cast_shadows,
            rotation_mode=rotation_mode, rotation=rotation, translation=translation, tag=tag
        )
        self._lights[tag] = light
        return light

    def add_sun(
            self,
            strength: float = 10,
            angular_diameter: float = 0.00918043,
            color: Vector3d = (1.0, 1.0, 1.0),
            cast_shadows=True,
            rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None,
            translation: Vector3d = (0, 0, 0),
            tag=None
    ) -> DirectionalLight:
        """Add DirectionalLight light source to the scene

        Args:
            strength (float, optional): strength of the light source in watts per meter squared (W/m^2) (default: 100)
            angular_diameter (float, optional): angular diameter of the Sun as seen from the Earth
                in [0, 3.14159] (default: 0.00918043)
            color (Vector3d, optional): color of the light source (default: (1.0, 1.0, 1.0))
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
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
            tag (str, optional): name of the created collection in Blender to represent the point cloud.
                If None is passed the tag is automatically generated (default: None)

        Returns:
            DirectionalLight: created and added to the scene object
        """
        # angular_diameter: Angular diameter of the Sun as seen from the Earth,  [0, 3.14159]
        tag = self._process_tag(tag, "Sun")
        light = DirectionalLight(
            color=color, strength=strength, angular_diameter=angular_diameter, cast_shadows=cast_shadows,
            rotation_mode=rotation_mode, rotation=rotation, translation=translation, tag=tag
        )
        self._lights[tag] = light
        return light

    def add_spot(
            self,
            strength: float = 100,
            spot_size: float = 0.785398,
            spot_blend: float = 0.15,
            shadow_soft_size: float = 0.25,
            color: Vector3d = (1.0, 1.0, 1.0),
            cast_shadows=True,
            rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None,
            translation: Vector3d = (0, 0, 0),
            tag=None
    ) -> SpotLight:
        """Add SpotLight light source to the scene

        Args:
            strength (float, optional): strength of the light source that light would emit over its entire area if
                it wasn't limited by the spot angle (default: 100)
            spot_size (float, optional): angle of the spotlight beam in [0.0174533, 3.14159] (default: 0.785398)
            spot_blend (float, optional): the softness of the spotlight edge in [0, 1] (default: 0.15)
            shadow_soft_size (float, optional): light size for ray shadow sampling (Raytraced shadows)
                in [0, inf] (default: 0.25)
            color (Vector3d, optional): color of the light source (default: (1.0, 1.0, 1.0))
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
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
            tag (str, optional): name of the created collection in Blender to represent the point cloud.
                If None is passed the tag is automatically generated (default: None)

        Returns:
            SpotLight: created and added to the scene object
        """
        tag = self._process_tag(tag, "Spot")
        light = SpotLight(
            color=color, strength=strength, spot_size=spot_size, spot_blend=spot_blend, cast_shadows=cast_shadows,
            shadow_soft_size=shadow_soft_size, rotation_mode=rotation_mode, rotation=rotation, translation=translation, tag=tag
        )
        self._lights[tag] = light
        return light

    def add_area(
            self,
            shape: str,
            size: Union[float, Vector2d],
            strength: float = 100,
            color: Vector3d = (1.0, 1.0, 1.0),
            cast_shadows=True,
            rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None,
            translation: Vector3d = (0, 0, 0),
            tag: str = None
    ) -> AreaLight:
        """Add AreaLight light source to the scene. Shape of the area is controlled by shape parameter

        Args:
            shape (str): type of the AreaLight, one of: [square, circle, rectangle, ellipse]
            size (Union[float, Vector2d]): size of the area of the area light for circle and square or
                [x, y] sizes of the area light for rectangle and ellipse
            strength (float, optional): strength of the light source emitted over the entire area of the light
                in all directions (default: 100)
            color (Vector3d, optional): color of the light source (default: (1.0, 1.0, 1.0))
            cast_shadows (bool, optional): whether the light source casts shadows or not (default: True)
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
            tag (str, optional): name of the created collection in Blender to represent the point cloud.
                If None is passed the tag is automatically generated (default: None)

        Returns:
            AreaLight: subclass of AreaLight (depending on shape), created and added to the scene
        """
        tag = self._process_tag(tag, "Area")
        if shape == "square":
            light = SquareAreaLight(
                size=size, color=color, strength=strength, cast_shadows=cast_shadows,
                rotation_mode=rotation_mode, rotation=rotation, translation=translation, tag=tag
            )
        elif shape == "circle":
            light = CircleAreaLight(
                size=size, color=color, strength=strength, cast_shadows=cast_shadows,
                rotation_mode=rotation_mode, rotation=rotation, translation=translation, tag=tag
            )
        elif shape == "rectangle":
            light = RectangleAreaLight(
                size=size, color=color, strength=strength, cast_shadows=cast_shadows,
                rotation_mode=rotation_mode, rotation=rotation, translation=translation, tag=tag
            )
        elif shape == "ellipse":
            light = EllipseAreaLight(
                size=size, color=color, strength=strength, cast_shadows=cast_shadows,
                rotation_mode=rotation_mode, rotation=rotation, translation=translation, tag=tag
            )
        else:
            raise NotImplementedError(f"Unknown AreaLight shape: {shape}")
        self._lights[tag] = light
        return light

    def _process_tag(self, tag: str, default_prefix: str = "Light"):
        lights_keys = self._lights.keys()

        if tag is None:
            _tag = default_prefix + "_{:03d}"
            index = 0
            while _tag.format(index) in lights_keys:
                index += 1
            tag = _tag.format(index)
        elif tag in lights_keys:
            raise RuntimeError(f"Object with tag {tag} is already in collection.")

        return tag

    def keys(self):
        return self._lights.keys()

    def values(self):
        return self._lights.values()

    def items(self):
        return self._lights.items()

    def remove(self, obj_or_tag: Union[Light, str]):
        assert isinstance(obj_or_tag, (Light, str)), "Only Light object or it's tag is allowed"
        if isinstance(obj_or_tag, str):
            tag = obj_or_tag
        else:
            obj = obj_or_tag
            tag = obj.tag
        self.__delitem__(tag)

    def __getitem__(self, key: str) -> Light:
        return self._lights[key]

    def __delitem__(self, key: str):
        self._lights[key]._blender_remove_object()
        del self._lights[key]

    def __iter__(self) -> Iterable:
        return iter(self._lights)

    def __len__(self) -> int:
        return len(self._lights)

    def _reset(self):
        self._lights = dict()
        self.remove_background_light()

    # def __str__(self):
    #     return str(self.__dict__)
    #
    # def __repr__(self):
    #     return '{}, D({})'.format(super(D, self).__repr__(), self.__dict__)
