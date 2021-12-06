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
        self._bl_mesh = mesh
        self._bl_obj = obj

    def _blender_set_visuals(self, visuals:Visuals):
        if isinstance(visuals, UniformColorVisuals):
            #TODO: Rewite uniform color though nodes to unify material creation routine
            object_material = bpy.data.materials.new('colored')
            object_material.diffuse_color = visuals.color
            object_material.specular_intensity = visuals.spec_intensity
        elif isinstance(visuals, VertexColorVisuals):
            bpy.context.view_layer.objects.active = self._bl_obj
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(self._bl_mesh)
            color_layer = bm.loops.layers.color.new("color")
            for face in bm.faces:
                for loop in face.loops:
                    loop[color_layer] = visuals.vertex_colors[loop.vert.index]
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.shade_smooth()
            object_material = bpy.data.materials.new('object_material')
            object_material.use_nodes = True
            bsdf = object_material.node_tree.nodes["Principled BSDF"]
            bsdf.inputs['Alpha'].default_value = visuals.alpha  # Set alpha
            bsdf.inputs['Specular'].default_value = visuals.spec_intensity
            vertex_color = object_material.node_tree.nodes.new('ShaderNodeVertexColor')
            object_material.node_tree.links.new(vertex_color.outputs[0], bsdf.inputs[0])
        elif isinstance(visuals, UVVisuals):
            bpy.context.view_layer.objects.active = self._bl_obj
            bpy.ops.object.mode_set(mode='EDIT')
            bm = bmesh.from_edit_mesh(self._bl_mesh)
            uv_layer = bm.loops.layers.uv.active
            for face in bm.faces:
                for loop in face.loops:
                    loop_uv = loop[uv_layer]
                    loop_uv.uv = visuals.uv_map[loop.vert.index].tolist()
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.shade_smooth()
            object_material = bpy.data.materials.new('object_material')
            object_material.use_nodes = True
            bsdf = object_material.node_tree.nodes["Principled BSDF"]
            bsdf.inputs['Alpha'].default_value = visuals.alpha
            bsdf.inputs['Specular'].default_value = visuals.spec_intensity
            object_texture = object_material.node_tree.nodes.new('ShaderNodeTexImage')
            if isinstance(visuals, FileTextureVisuals):
                object_texture.image = visuals.texture_path
            elif isinstance(visuals, TextureVisuals):
                raise NotImplementedError("Assinging textures from memory is not implemented yet")
            else:
                raise NotImplementedError(f"Unknown visuals type {visuals.__class__.__name__}")
            object_material.node_tree.links.new(bsdf.inputs['Base Color'], object_texture.outputs['Color'])
        else:
            raise NotImplementedError(f"Unknown visuals type {visuals.__class__.__name__}")
        self._bl_obj.active_material = object_material

    def __init__(self, vertices:np.ndarray, faces:np.ndarray, visuals:Visuals, tag:str):
        super().__init__(tag)
        self._blender_create_mesh(vertices, faces)
        self._blender_set_visuals(visuals)

    def update_visuals(self, visuals: Visuals):
        material = self._bl_obj.active_material
        material.user_clear()
        bpy.data.materials.remove(material)
        self._blender_set_visuals(visuals)
