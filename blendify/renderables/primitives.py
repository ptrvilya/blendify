from abc import abstractmethod

import bpy
import numpy as np

from .base import RenderableObject
from ..colors import UniformColors
from ..colors.base import Colors
from ..internal.types import Vector3d
from ..materials.base import Material


# =================================================== Mesh Primitives ==================================================
class MeshPrimitive(RenderableObject):
    """Base class for mesh primitives. Used to throw Exceptions for non-implemented Colors
    subclasses (only UniformColors is supported) and add shared method for setting smooth shading.

    Properties:
        emit_shadow (bool, optional): control whether the object will emit shadow from any light source in the scene.

    Methods:
        set_smooth(bool): turns smooth shading on and off based on the bool argument.
    """
    @abstractmethod
    def __init__(
        self,
        **kwargs
    ):
        """Passes all arguments to the constructor of the base class

        Args:
            material (Material): Material instance
            colors (Colors): Colors instance
            blender_object (bpy.types.Object): instance of Blender Object that is wrapped by the class
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        super().__init__(**kwargs)

    def _blender_set_colors(self, colors: Colors):
        if not isinstance(colors, UniformColors):
            raise NotImplementedError("Non-uniform colors or textures are not supported in primitives, "
                                      "consider creating a primitive through Mesh for that")
        super()._blender_set_colors(colors)

    def set_smooth(self, smooth: bool = True):
        """Enables or disables the smooth surface imitation for the object

        Args:
            smooth (bool): Whether to turn the smooth surface on or off
        """
        bpy.context.view_layer.objects.active = self._blender_object
        bpy.ops.object.mode_set(mode='OBJECT')
        if smooth:
            bpy.ops.object.shade_smooth()
        else:
            bpy.ops.object.shade_flat()


class CubeMesh(MeshPrimitive):
    """Cube mesh primitive, supports only uniform coloring (UniformColors)

    Properties:
        emit_shadow (bool, optional): control whether the object will emit shadow from any light source in the scene.

    Methods:
        set_smooth(bool): turns smooth shading on and off based on the bool argument.
    """
    def __init__(
        self,
        size: float,
        tag: str,
        **kwargs
    ):
        """Creates Blender Object that represent Cube mesh primitive

        Args:
            size (float): size of a primitive in [0, inf]
            material (Material): Material instance
            colors (Colors): Colors instance
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        obj = self._blender_create_object(size, tag)
        super().__init__(**kwargs, blender_object=obj, tag=tag)

    def _blender_create_object(
        self,
        size: float,
        tag: str
    ):
        bpy.ops.mesh.primitive_cube_add(size=size)
        obj = bpy.context.object
        obj.name = tag
        return obj

    def _blender_set_colors(
        self,
        colors: Colors
    ):
        """Remembers current color properties, builds a color node for material, sets color information to mesh

        Args:
            colors (Colors): target colors information
        """
        bpy.context.view_layer.objects.active = self._blender_object
        bpy.ops.object.shade_smooth()
        # bpy.context.space_data.context = 'MODIFIER'
        bpy.ops.object.modifier_add(type='EDGE_SPLIT')
        super()._blender_set_colors(colors)


class CircleMesh(MeshPrimitive):
    """Circle mesh primitive, supports only uniform coloring (UniformColors)

    Properties:
        emit_shadow (bool, optional): control whether the object will emit shadow from any light source in the scene

    Methods:
        set_smooth(bool): turns smooth shading on and off based on the bool argument.
    """
    def __init__(
        self,
        radius: float,
        tag: str,
        num_vertices: int = 32,
        fill_type: str = "NGON",
        **kwargs
    ):
        """Creates Blender Object that represent Circle mesh primitive

        Args:
            radius (float): radius of a primitive in [0, inf]
            material (Material): Material instance
            colors (Colors): Colors instance
            num_vertices (int, optional): number of vertices in primitive in [3, 10000000] (default: 32)
            fill_type (str, optional): fill type, one of [NOTHING, NGON, TRIFAN] (default: NGON)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        obj = self._blender_create_object(num_vertices, radius, fill_type, tag)
        super().__init__(**kwargs, blender_object=obj, tag=tag)

    def _blender_create_object(
        self,
        num_vertices: int,
        radius: float,
        fill_type: str,
        tag: str
    ):
        bpy.ops.mesh.primitive_circle_add(vertices=num_vertices, radius=radius, fill_type=fill_type)
        obj = bpy.context.object
        obj.name = tag
        return obj

    def _blender_set_colors(
        self,
        colors: Colors
    ):
        """Remembers current color properties, builds a color node for material, sets color information to mesh

        Args:
            colors (Colors): target colors information
        """
        bpy.context.view_layer.objects.active = self._blender_object
        bpy.ops.object.shade_smooth()
        # bpy.context.space_data.context = 'MODIFIER'
        bpy.ops.object.modifier_add(type='EDGE_SPLIT')
        super()._blender_set_colors(colors)


class CylinderMesh(MeshPrimitive):
    """Cylinder mesh primitive, supports only uniform coloring (UniformColors)

    Properties:
        emit_shadow (bool, optional): control whether the object will emit shadow from any light source in the scene.

    Methods:
        set_smooth(bool): turns smooth shading on and off based on the bool argument.
    """
    def __init__(
        self,
        radius: float,
        height: float,
        tag: str,
        num_vertices: int = 32,
        fill_type: str = "NGON",
        **kwargs
    ):
        """Creates Blender Object that represent Cylinder mesh primitive

        Args:
            radius (float): radius of a primitive in [0, inf]
            height (float): height of a primitive in [0, inf]
            material (Material): Material instance
            colors (Colors): Colors instance
            num_vertices (int, optional): number of vertices in primitive in [3, 10000000] (default: 32)
            fill_type (str, optional): fill type, one of [NOTHING, NGON, TRIFAN] (default: NGON)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        obj = self._blender_create_object(num_vertices, radius, height, fill_type, tag)
        # obj.scale[2] = height / radius
        super().__init__(**kwargs, blender_object=obj, tag=tag)

    def _blender_create_object(
        self,
        num_vertices: int,
        radius: float,
        height: float,
        fill_type: str,
        tag: str
    ):
        bpy.ops.mesh.primitive_cylinder_add(vertices=num_vertices, radius=radius, depth=height, end_fill_type=fill_type)
        obj = bpy.context.object
        obj.name = tag
        return obj

    def _blender_set_colors(
            self,
            colors: Colors
    ):
        """Remembers current color properties, builds a color node for material, sets color information to mesh

        Args:
            colors (Colors): target colors information
        """
        bpy.context.view_layer.objects.active = self._blender_object
        bpy.ops.object.shade_smooth()
        # bpy.context.space_data.context = 'MODIFIER'
        bpy.ops.object.modifier_add(type='EDGE_SPLIT')
        super()._blender_set_colors(colors)
# =============================================== End of Mesh Primitives ===============================================


# ================================================ Parametric Primitives ===============================================
class ParametricPrimitive(RenderableObject):
    """Base class for parametric primitives. Used to throw Exceptions for non-implemented Colors
    subclasses (only UniformColors is supported)

    Properties:
        emit_shadow (bool, optional): control whether the object will emit shadow from any light source in the scene.
    """

    @abstractmethod
    def __init__(
        self,
        **kwargs
    ):
        """Passes all arguments to the constructor of the base class

        Args:
            material (Material): Material instance
            colors (Colors): Colors instance
            blender_object (bpy.types.Object): instance of Blender Object that is wrapped by the class
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        super().__init__(**kwargs)

    def _blender_set_colors(self, colors: Colors):
        if not isinstance(colors, UniformColors):
            raise NotImplementedError("Non-uniform colors or textures are not supported in primitives, "
                                      "consider creating a primitive through Mesh for that")
        super()._blender_set_colors(colors)


class EllipsoidNURBS(ParametricPrimitive):
    """NURBS Ellipsoid, implemented as NURBS Sphere that is rescaled along axes,
     supports only uniform coloring (UniformColors)

    Properties:
        emit_shadow (bool, optional): control whether the object will emit shadow from any light source in the scene
    """
    def __init__(
        self,
        radius: Vector3d,
        tag: str,
        **kwargs
    ):
        """Creates Blender Object that represent NURBS Surface Sphere primitive with different scales along axis,
        resulting in Ellipsoid shape

        Args:
            radius (float): radius of a primitive in [0, inf]
            material (Material): Material instance
            colors (Colors): Colors instance
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        obj = self._blender_create_object(radius, tag)
        super().__init__(**kwargs, blender_object=obj, tag=tag)

    def _blender_create_object(
            self,
            radius: Vector3d,
            tag: str
    ):
        bpy.ops.surface.primitive_nurbs_surface_sphere_add(radius=radius[0])
        obj = bpy.context.object
        obj.scale = (np.array(radius) / radius[0]).tolist()
        obj.name = tag
        return obj


class SphereNURBS(EllipsoidNURBS):
    """NURBS Sphere, supports only uniform coloring (UniformColors)

    Properties:
        emit_shadow (bool, optional): control whether the object will emit shadow from any light source in the scene
    """
    def __init__(
        self,
        radius: float,
        tag: str,
        **kwargs
    ):
        """Creates Blender Object that represent NURBS Surface Sphere primitive

        Args:
            radius (float): radius of a primitive in [0, inf]
            material (Material): Material instance
            colors (Colors): Colors instance
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        super().__init__(**kwargs, radius=(radius, radius, radius), tag=tag)


class CurveBezier(ParametricPrimitive):
    """Bezier Curve, supports only uniform coloring (UniformColors)

    Properties:
        emit_shadow (bool, optional): control whether the object will emit shadow from any light source in the scene
    """
    def __init__(
        self,
        keypoints: np.ndarray,
        radius: float,
        tag: str,
        **kwargs
    ):
        """Creates Blender Object that represent Bezier Curve primitive - a tube passing through the given keypoints

        Args:
            keypoints (np.ndarray): keypoints for the curve
            radius (float): radius of a tube in [0, inf]
            material (Material): Material instance
            colors (Colors): Colors instance
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        obj = self._blender_create_object(tag)
        obj.data.bevel_depth = radius
        obj.data.bevel_resolution = 4
        if len(keypoints) > 2:
            obj.data.splines[0].bezier_points.add(count=len(keypoints) - 2)
        for ind, coords in enumerate(keypoints):
            obj.data.splines[0].bezier_points[ind].co = coords
            obj.data.splines[0].bezier_points[ind].handle_left_type = 'VECTOR'
            obj.data.splines[0].bezier_points[ind].handle_right_type = 'VECTOR'
        super().__init__(**kwargs, blender_object=obj, tag=tag)

    def _blender_create_object(
        self,
        tag: str
    ):
        bpy.ops.curve.primitive_bezier_curve_add()
        obj = bpy.context.object
        obj.data.dimensions = '3D'
        obj.data.fill_mode = 'FULL'
        return obj
# ============================================ End of Parametric Primitives ============================================
