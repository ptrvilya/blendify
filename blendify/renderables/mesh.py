import bpy
import bmesh
import numpy as np
from .base import Renderable
from .materials import Material
from .colors import Colors, VertexColors, UniformColors, UVColors, TextureColors, FileTextureColors


class Mesh(Renderable):
    def _blender_create_mesh(self, vertices, faces):
        mesh = bpy.data.meshes.new(name=self.tag)
        mesh.from_pydata(vertices.tolist(), [], faces.tolist())
        obj = bpy.data.objects.new(self.tag, mesh)
        bpy.context.collection.objects.link(obj)
        self._blender_mesh = mesh
        return obj

    def _blender_set_colors(self, colors: Colors):
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
            bm = bmesh.from_edit_mesh(self._blender_mesh)
            uv_layer = bm.loops.layers.uv.active
            for face in bm.faces:
                for loop in face.loops:
                    loop_uv = loop[uv_layer]
                    loop_uv.uv = colors.uv_map[loop.vert.index].tolist()
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.shade_smooth()
        elif not isinstance(colors, UniformColors):
            raise NotImplementedError(f"Unknown visuals type {colors.__class__.__name__}")
        super()._blender_set_colors(colors)

    def _blender_clear_colors(self):
        material = self._blender_object.active_material
        if material is not None:
            material.user_clear()
            bpy.data.materials.remove(material)

    def __init__(self, vertices: np.ndarray, faces: np.ndarray, material: Material, colors: Colors,  tag: str):
        obj = self._blender_create_mesh(vertices, faces)
        super().__init__(material, colors, tag, obj)

    def update_vertices(self, vertices: np.ndarray):
        for ind, vert in enumerate(self._blender_mesh.vertices):
            vert.co = vertices[ind]
        self._blender_mesh.update()

