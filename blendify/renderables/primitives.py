import bpy
import bpy_types
import bmesh
import numpy as np
from ..internal.types import Vector3d, Vector4d
from .base import Renderable, RenderableObject
from .materials import Material
from .colors import Colors, VertexColors, UniformColors, UVColors, TextureColors, FileTextureColors


class PrimitiveNURBS(RenderableObject):
    def __init__(self, material: Material, colors: Colors, tag: str, blender_object: bpy_types.Object,
            quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0)):
        super().__init__(material, colors, tag, blender_object, quaternion, translation)

    def _blender_set_colors(self, colors: Colors):
        if not isinstance(colors, UniformColors):
            raise NotImplementedError("Non-uniform colors or textures are not supported in primitives, "
                                      "consider creating a primitive through Mesh for that")
        super()._blender_set_colors(colors)


class EllipsoidNURBS(PrimitiveNURBS):
    def __init__(self, radius: Vector3d, material: Material, colors: Colors, tag: str,
            quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0)):
        obj = self._blender_create_object(radius, tag)
        super().__init__(material, colors, tag, obj, quaternion, translation)

    def _blender_create_object(self, radius: Vector3d, tag: str):
        bpy.ops.surface.primitive_nurbs_surface_sphere_add(radius=radius[0])
        obj = bpy.context.object
        obj.scale = (np.array(radius) / radius[0]).tolist()
        obj.name = tag
        return obj


class SphereNURBS(EllipsoidNURBS):
    def __init__(self, radius: float, material: Material, colors: Colors, tag: str,
            quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0)):
        super().__init__((radius, radius, radius), material, colors, tag, quaternion, translation)


class CurveNURBS(PrimitiveNURBS):
    def __init__(self, keypoints: np.ndarray, radius: float, material: Material, colors: Colors, tag: str,
            quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0)):
        obj = self._blender_create_object(tag)
        obj.data.bevel_depth = radius
        obj.data.bevel_resolution = 4
        if len(keypoints) > 2:
            obj.data.splines[0].bezier_points.add(count=len(keypoints) - 2)
        for ind, coords in enumerate(keypoints):
            obj.data.splines[0].bezier_points[ind].co = coords
            obj.data.splines[0].bezier_points[ind].handle_left_type = 'VECTOR'
            obj.data.splines[0].bezier_points[ind].handle_right_type = 'VECTOR'
        super().__init__(material, colors, tag, obj, quaternion, translation)

    def _blender_create_object(self, tag: str):
        bpy.ops.curve.primitive_bezier_curve_add()
        obj = bpy.context.object
        obj.data.dimensions = '3D'
        obj.data.fill_mode = 'FULL'
        return obj


class CircleMesh(RenderableObject):
    def __init__(self, radius: float, material: Material, colors: Colors, tag: str,
                 vertices: int = 32, fill_type: str = "NGON",
                 quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0)):
        obj = self._blender_create_object(vertices, radius, fill_type, tag)
        super().__init__(material, colors, tag, obj, quaternion, translation)

    def _blender_create_object(self, vertices: int, radius: float, fill_type: str, tag: str):
        bpy.ops.mesh.primitive_circle_add(vertices=vertices, radius=radius, fill_type=fill_type)
        obj = bpy.context.object
        obj.name = tag
        return obj

    def _blender_set_colors(self, colors: Colors):
        """
        Remembers current color properties, builds a color node for material, sets color information to mesh
        Args:
            colors (Colors): target colors information
        """
        bpy.context.view_layer.objects.active = self._blender_object
        bpy.ops.object.shade_smooth()
        # bpy.context.space_data.context = 'MODIFIER'
        bpy.ops.object.modifier_add(type='EDGE_SPLIT')
        super()._blender_set_colors(colors)


class CylinderMesh(RenderableObject):
    def __init__(self, radius: float, height: float, material: Material, colors: Colors, tag: str, vertices: int = 32,
                 fill_type: str = "NGON", quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0)):
        obj = self._blender_create_object(vertices, radius, height, fill_type, tag)
        # obj.scale[2] = height / radius
        super().__init__(material, colors, tag, obj, quaternion, translation)

    def _blender_create_object(self, vertices: int, radius: float, height: float, fill_type: str, tag: str):
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=height, end_fill_type=fill_type)
        obj = bpy.context.object
        obj.name = tag
        return obj

    def _blender_set_colors(self, colors: Colors):
        """
        Remembers current color properties, builds a color node for material, sets color information to mesh
        Args:
            colors (Colors): target colors information
        """
        bpy.context.view_layer.objects.active = self._blender_object
        bpy.ops.object.shade_smooth()
        # bpy.context.space_data.context = 'MODIFIER'
        bpy.ops.object.modifier_add(type='EDGE_SPLIT')
        super()._blender_set_colors(colors)
