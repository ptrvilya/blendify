import bpy
import bpy_types
import bmesh
import numpy as np
from blendify.internal.types import Vector3d
from .base import Renderable, RenderableObject
from .materials import Material
from .colors import Colors, VertexColors, UniformColors, UVColors, TextureColors, FileTextureColors


class Primitive(RenderableObject):
    def __init__(self, material: Material, colors: Colors, tag: str, blender_object: bpy_types.Object):
        super().__init__(material, colors, tag, blender_object)

    def _blender_set_colors(self, colors: Colors):
        if not isinstance(colors, UniformColors):
            raise NotImplementedError("Non-uniform colors or textures are not supported in primitives, "
                                      "consider creating a primitive through Mesh for that")
        super()._blender_set_colors(colors)


class Ellipsoid(Primitive):
    def __init__(self, radius: Vector3d, material: Material, colors: Colors, tag: str):
        obj = self._blender_create_object(radius, tag)
        super().__init__(material, colors, tag, obj)

    def _blender_create_object(self, radius: Vector3d, tag: str):
        bpy.ops.surface.primitive_nurbs_surface_sphere_add(radius=radius[0])
        obj = bpy.context.object
        obj.scale = (np.array(radius) / radius[0]).tolist()
        obj.name = tag
        return obj


class Sphere(Ellipsoid):
    def __init__(self, radius: float, material: Material, colors: Colors, tag: str):
        super().__init__((radius, radius, radius), material, colors, tag)


class Curve(Primitive):
    def __init__(self, keypoints: np.ndarray, radius: float, material: Material, colors: Colors, tag: str):
        obj = self._blender_create_object(tag)
        obj.data.bevel_depth = radius
        obj.data.bevel_resolution = 4
        if len(keypoints) > 2:
            obj.data.splines[0].bezier_points.add(count=len(keypoints) - 2)
        for ind, coords in enumerate(keypoints):
            obj.data.splines[0].bezier_points[ind].co = coords
            obj.data.splines[0].bezier_points[ind].handle_left_type = 'VECTOR'
            obj.data.splines[0].bezier_points[ind].handle_right_type = 'VECTOR'
        super().__init__(material, colors, tag, obj)

    def _blender_create_object(self, tag: str):
        bpy.ops.curve.primitive_bezier_curve_add()
        obj = bpy.context.object
        obj.data.dimensions = '3D'
        obj.data.fill_mode = 'FULL'
        return obj


class Circle(Primitive):
    def __init__(self, radius: float, material: Material, colors: Colors, tag: str):
        obj = self._blender_create_object(radius, tag)
        super().__init__(material, colors, tag, obj)

    def _blender_create_object(self, radius: float, tag: str):
        bpy.ops.surface.primitive_nurbs_surface_circle_add(radius=radius)
        obj = bpy.context.object
        obj.name = tag
        return obj


class Cylinder(Primitive):
    def __init__(self, radius: float, height: float, material: Material, colors: Colors, tag: str):
        obj = self._blender_create_object(radius, tag)
        obj.scale[2] = height / radius
        super().__init__(material, colors, tag, obj)

    def _blender_create_object(self, radius: float, tag: str):
        bpy.ops.surface.primitive_nurbs_surface_cylinder_add(radius=radius)
        obj = bpy.context.object
        obj.name = tag
        return obj
