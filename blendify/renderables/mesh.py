from typing import Sequence

import bmesh
import bpy
import numpy as np

from .base import RenderableObject
from ..colors import VertexColors, UniformColors
from ..colors.base import ColorsList
from ..colors.texture import VertexUV, FacesUV, UVColors


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
            faces_material: Sequence[Sequence[int]] = None,
            **kwargs
    ):
        """Creates Blender Object that represent given mesh

        Args:
            vertices (np.ndarray): mesh vertices
            faces (np.ndarray): mesh faces
            material (Union[Material, MaterialList]): Material instance or a list of Material instances
            colors (Union[Colors, ColorsList]): Colors instance or a list of Colors instances
            quaternion (Vector4d, optional): rotation applied to Blender object (default: None (identity))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
            faces_material (np.ndarray, optional): for each face, the material index assigned to it
        """
        obj = self._blender_create_object(vertices, faces, tag)
        self._faces_material = faces_material
        self._faces_count = len(faces)
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
            colors_list: ColorsList
    ):
        """Remembers current color properties, builds a color node for material, sets color information to mesh

        Args:
            colors_list (ColorsList): list of target colors
        """
        for colors in colors_list:
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
        super()._blender_set_colors(colors_list)

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

    def _blender_assign_materials(self):
        super()._blender_assign_materials()
        assert self._faces_material is None or (len(self._faces_material) == self._faces_count), \
            f"Number of material faces should be equal to the number of faces ({self._faces_count})"
        if not (len(self._material_instances) == 1 or self._faces_material is None):
            bpy.context.view_layer.objects.active = self._blender_object
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='FACE')
            bpy.ops.mesh.select_all(action='DESELECT')
            bm = bmesh.from_edit_mesh(self._blender_mesh)
            for mat_ind in range(self._materials_count):
                for face in bm.faces:
                    perface_mat_ind = self._faces_material[face.index]
                    if perface_mat_ind == mat_ind:
                        face.select = True
                self._blender_object.active_material_index = mat_ind
                bpy.ops.object.material_slot_assign()
                bpy.ops.mesh.select_all(action='DESELECT')
            # bmesh.update_edit_mesh(self._blender_object.data)
            bpy.ops.object.mode_set(mode='OBJECT')

