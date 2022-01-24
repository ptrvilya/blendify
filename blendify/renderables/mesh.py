import bpy
import bpy_types
import bmesh
import numpy as np
from .base import RenderableObject
from .materials import Material
from .colors import Colors, VertexColors, UniformColors, UVColors, TextureColors, FileTextureColors
from ..internal.types import Vector3d, Vector4d


class Mesh(RenderableObject):
    def __init__(self, vertices: np.ndarray, faces: np.ndarray, material: Material, colors: Colors, tag: str,
            quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0)):
        obj = self._blender_create_object(vertices, faces, tag)
        super().__init__(material, colors, tag, obj, quaternion, translation)

    """
    Basic mesh with vertices and faces, supports any coloring
    """
    def _blender_create_object(self, vertices:np.ndarray, faces:np.ndarray, tag: str) -> bpy_types.Object:
        """
        Creates mesh object in Blender
        Args:
            vertices (np.ndarray): mesh vertices
            faces (np.ndarray): mesh faces
        Returns:
            bpy_types.Object: Blender mesh
        """
        mesh = bpy.data.meshes.new(name=tag)
        mesh.from_pydata(vertices.tolist(), [], faces.tolist())
        obj = bpy.data.objects.new(tag, mesh)
        bpy.context.collection.objects.link(obj)
        self._blender_mesh = mesh
        return obj

    def _blender_set_colors(self, colors: Colors):
        """
        Remembers current color properties, builds a color node for material, sets color information to mesh
        Args:
            colors (Colors): target colors information
        """
        if isinstance(colors, VertexColors):
            bpy.context.view_layer.objects.active = self._blender_object
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(self._blender_mesh)
            color_layer = bm.loops.layers.color.new("color")
            for face in bm.faces:
                for loop in face.loops:
                    loop[color_layer] = colors.vertex_colors[loop.vert.index]
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.shade_smooth()
        elif isinstance(colors, UVColors):
            bpy.context.view_layer.objects.active = self._blender_object
            bpy.ops.object.mode_set(mode='EDIT')
            self._blender_mesh.uv_layers.new(name='NewUVMap')
            bm = bmesh.from_edit_mesh(self._blender_mesh)
            uv_layer = bm.loops.layers.uv.active
            print(self._blender_object, bm)
            for face in bm.faces:
                for loop in face.loops:
                    loop_uv = loop[uv_layer]
                    loop_uv.uv = colors.uv_map[loop.vert.index].tolist()
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.shade_smooth()
        elif not isinstance(colors, UniformColors):
            raise NotImplementedError(f"Unknown visuals type {colors.__class__.__name__}")
        super()._blender_set_colors(colors)

    def update_vertices(self, vertices: np.ndarray):
        """
        Updates mesh vertices coordinates
        Args:
            vertices: new vertex coordinates
        """
        assert len(self._blender_mesh.vertices) == len(vertices), \
            f"Number of vertices should be the same (expected {len(self._blender_mesh.vertices)}, got {len(vertices)})"
        for ind, vert in enumerate(self._blender_mesh.vertices):
            vert.co = vertices[ind]
        self._blender_mesh.update()
