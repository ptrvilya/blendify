import bmesh
import bpy
import numpy as np

from .base import RenderableObject
from ..colors import VertexColors, UniformColors
from ..colors.base import Colors
from ..colors.texture import VertexUV, FacesUV, UVColors
from ..materials.base import Material


class Mesh(RenderableObject):
    """Basic mesh, supports uniform (UniformColors), per-vertex (VertexColors)
    and texture (TextureColors and FileTextureColors) coloring with per-vertex uv (VertexUV) or
    per-face uv maps (FacesUV).

    Properties:
        emit_shadow (bool, optional): control whether mesh will emit shadow from any light source in the scene
    """

    def __init__(
            self,
            vertices: np.ndarray,
            faces: np.ndarray,
            tag: str,
            **kwargs
    ):
        """Creates Blender Object that represent given mesh

        Args:
            vertices (np.ndarray): mesh vertices
            faces (np.ndarray): mesh faces
            material (Material): Material instance
            colors (Colors): Colors instance
            quaternion (Vector4d, optional): rotation applied to Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        obj = self._blender_create_object(vertices, faces, tag)
        super().__init__(**kwargs, blender_object=obj, tag=tag)

    def _blender_create_object(
            self,
            vertices: np.ndarray,
            faces: np.ndarray,
            tag: str
    ) -> bpy.types.Object:
        """Creates mesh object in Blender

        Args:
            vertices (np.ndarray): mesh vertices
            faces (np.ndarray): mesh faces

        Returns:
            bpy.types.Object: Blender mesh
        """
        mesh = bpy.data.meshes.new(name=tag)
        mesh.from_pydata(vertices.tolist(), [], faces.tolist())
        obj = bpy.data.objects.new(tag, mesh)
        bpy.context.collection.objects.link(obj)
        self._blender_mesh = mesh
        return obj

    def set_smooth(self, smooth: bool = True):
        """Turns smooth shading on and off based on the bool argument

        Args:
            smooth (bool, optional): If True shade smooth else shade flat (default: True)
        """
        bpy.context.view_layer.objects.active = self._blender_object
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(self._blender_mesh)
        for face in bm.faces:
            face.smooth = smooth
        bpy.ops.object.mode_set(mode='OBJECT')
        if smooth:
            bpy.ops.object.shade_smooth()
        else:
            bpy.ops.object.shade_flat()

    def _blender_set_colors(
            self,
            colors: Colors
    ):
        """Remembers current color properties, builds a color node for material, sets color information to mesh

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
            self._blender_mesh.vertex_colors["color"].active_render = True
        elif isinstance(colors, UVColors):
            bpy.context.view_layer.objects.active = self._blender_object
            bpy.ops.object.mode_set(mode='EDIT')
            self._blender_mesh.uv_layers.new(name='NewUVMap')
            bm = bmesh.from_edit_mesh(self._blender_mesh)
            uv_layer = bm.loops.layers.uv.active
            uv_map = colors.uv_map
            if isinstance(uv_map, VertexUV):
                for face in bm.faces:
                    for loop in face.loops:
                        loop_uv = loop[uv_layer]
                        loop_uv.uv = uv_map.data[loop.vert.index].tolist()
            elif isinstance(uv_map, FacesUV):
                for face in bm.faces:
                    face_uv = uv_map.data[face.index]
                    for loop, loop_uv_coords in zip(face.loops, face_uv):
                        loop[uv_layer].uv = loop_uv_coords.tolist()
            else:
                raise NotImplementedError(f"Unknown UV map type: {uv_map.__class__.__name__}")
            bpy.ops.object.mode_set(mode='OBJECT')
        elif not isinstance(colors, UniformColors):
            raise NotImplementedError(f"Unknown Colors type {colors.__class__.__name__}")
        super()._blender_set_colors(colors)

    def update_vertices(
            self,
            vertices: np.ndarray
    ):
        """Updates mesh vertices coordinates

        Args:
            vertices (np.ndarray): new vertex coordinates
        """
        assert len(self._blender_mesh.vertices) == len(vertices), \
            f"Number of vertices should be the same (expected {len(self._blender_mesh.vertices)}, got {len(vertices)})"
        for ind, vert in enumerate(self._blender_mesh.vertices):
            vert.co = vertices[ind]
        self._blender_mesh.update()
