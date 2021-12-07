import bpy
import bmesh
import numpy as np
from .base import Renderable
from .visuals import Visuals, VertexColorVisuals, UniformColorVisuals, UVVisuals, TextureVisuals, FileTextureVisuals


class Mesh(Renderable):
    def _blender_create_mesh(self, vertices, faces):
        mesh = bpy.data.meshes.new(name=self.tag)
        mesh.from_pydata(vertices.tolist(), [], faces.tolist())
        obj = bpy.data.objects.new(self.tag, mesh)
        bpy.context.collection.objects.link(obj)
        self._blender_mesh = mesh
        return obj

    def _blender_set_visuals(self, visuals: Visuals):
        if isinstance(visuals, VertexColorVisuals):
            bpy.context.view_layer.objects.active = self._blender_object
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(self._blender_mesh)
            color_layer = bm.loops.layers.color.new("color")
            for face in bm.faces:
                for loop in face.loops:
                    loop[color_layer] = visuals.vertex_colors[loop.vert.index]
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.shade_smooth()
        elif isinstance(visuals, UVVisuals):
            bpy.context.view_layer.objects.active = self._blender_object
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(self._blender_mesh)
            uv_layer = bm.loops.layers.uv.active
            for face in bm.faces:
                for loop in face.loops:
                    loop_uv = loop[uv_layer]
                    loop_uv.uv = visuals.uv_map[loop.vert.index].tolist()
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.shade_smooth()
        elif not isinstance(visuals, UniformColorVisuals):
            raise NotImplementedError(f"Unknown visuals type {visuals.__class__.__name__}")
        object_material = visuals.create_material()
        self._blender_object.active_material = object_material

    def _blender_clear_visuals(self):
        material = self._blender_object.active_material
        if material is not None:
            material.user_clear()
            bpy.data.materials.remove(material)

    def __init__(self, vertices: np.ndarray, faces: np.ndarray, visuals: Visuals, tag: str):
        obj = self._blender_create_mesh(vertices, faces)
        super().__init__(visuals, tag, obj)
