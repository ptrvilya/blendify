import numpy as np
import bpy_types
import bpy
from typing import Union, Tuple, List, Sequence
from abc import ABC, abstractmethod
from ..cameras import Camera
from .colors import Colors, UniformColors, VertexColors, TextureColors, FileTextureColors
from .materials import Material
from ..internal.positionable import Positionable
from ..internal.types import BlenderGroup


class Renderable(Positionable):
    class ColorsNodeBuilder(ABC):
        colors_class = None
        @abstractmethod
        def __call__(self, object_material: bpy.types.Material):
            return None

    class UniformColorsNodeBuilder(ColorsNodeBuilder):
        colors_class = UniformColors

        def __init__(self, color: np.ndarray):
            self.color = color

    class VertexColorsNodeBuilder(ColorsNodeBuilder):
        colors_class = VertexColors

    class TextureColorsNodeBuilder(ColorsNodeBuilder):
        colors_class = TextureColors

        def __init__(self, texture: np.ndarray):
            self.texture = texture

    class FileTextureColorsNodeBuilder(ColorsNodeBuilder):
        colors_class = FileTextureColors

        def __init__(self, texture_path: str):
            self.texture_path = texture_path

    @abstractmethod
    def __init__(self, material: Material, colors: Colors, tag: str, blender_object: BlenderGroup):
        super().__init__(tag, blender_object)
        self._make_colorsnode_builders_dict()
        self.update_material(material)
        self.update_colors(colors)

    def _make_colorsnode_builders_dict(self):
        colorsnode_builders = {}
        for attrname in dir(self):
            attr = getattr(self, attrname)
            if isinstance(attr, self.ColorsNodeBuilder):
                colorsnode_builders[attr.colors_class] = attr
        self._colorsnode_builders = colorsnode_builders

    def get_colorsnode_builder(self, colors:Colors):
        builder_class = self._colorsnode_builders[colors.__class__]
        if isinstance(colors, UniformColors):
            builder = builder_class(colors.color)
        elif isinstance(colors, VertexColors):
            builder = builder_class()
        elif isinstance(colors, TextureColors):
            builder = builder_class(colors.texture)
        elif isinstance(colors, FileTextureColors):
            builder = builder_class(colors.texture_path)
        else:
            raise NotImplementedError(f"Unknown colors class '{colors.__class__.__name__}'")
        return builder

    def update_material(self, material: Material):
        """
        Updates object material properties, sets Blender structures accordingly
        Args:
            material (Material): target material
        """
        pass

    def update_colors(self, colors: Colors):
        """
        Updates object color properties, sets Blender structures accordingly
        Args:
            colors (Colors): target colors information
        """
        pass


class RenderableCollection(Renderable):
    def __init__(self, material: Material, colors: Colors, tag: str, blender_object: bpy.types.Collection):
        super().__init__(material, colors, tag, blender_object)


class RenderableObject(Renderable):
    class UniformColorsNodeBuilder(Renderable.UniformColorsNodeBuilder):
        def __call__(self, object_material: bpy.types.Material):
            color_node = object_material.node_tree.nodes.new('ShaderNodeRGB')
            color_node.outputs[0].default_value = self.color.tolist() + [1.]
            return color_node

    class VertexColorsNodeBuilder(Renderable.VertexColorsNodeBuilder):
        def __call__(self, object_material: bpy.types.Material):
            vertex_color_node = object_material.node_tree.nodes.new('ShaderNodeVertexColor')
            return vertex_color_node

    class TextureColorsNodeBuilder(Renderable.TextureColorsNodeBuilder):
        def __call__(self, object_material: bpy.types.Material):
            object_texture = object_material.node_tree.nodes.new('ShaderNodeTexImage')
            # <Texture creation goes here>
            return object_texture

    class FileTextureColorsNodeBuilder(Renderable.FileTextureColorsNodeBuilder):
        def __call__(self, object_material: bpy.types.Material):
            object_texture = object_material.node_tree.nodes.new('ShaderNodeTexImage')
            object_texture.image = self.texture_path
            return object_texture

    @abstractmethod
    def __init__(self, material: Material, colors: Colors, tag: str, blender_object: bpy_types.Object):
        self._blender_colornode_builder = None
        self._blender_colors_node = None
        self._blender_material_node = None
        self._blender_bsdf_node = None
        super().__init__(material, colors, tag, blender_object)

    def update_camera(self, camera: Camera):
        """
        Updates object based on current camera position
        Args:
            camera (Camera): target camera
        """
        pass

    def _blender_clear_colors(self):
        """
        Clears Blender color node and erases node constructor
        """
        if self._blender_colors_node is not None:
            self._blender_colors_node.user_clear()
            self._blender_colors_node = None
            self._blender_colornode_builder = None

    def _blender_set_colors(self, colors: Colors):
        """
        Remembers current color properies, builds a color node for material
        Args:
            colors (Colors): target colors information
        """
        self._blender_colornode_builder = self.get_colorsnode_builder(colors)
        self._blender_create_colornode()

    def _blender_create_colornode(self):
        """
        Creates color node using previously set builder
        """
        if self._blender_colornode_builder is not None:
            self._blender_colors_node = self._blender_colornode_builder(self._blender_material_node)
            self._blender_link_color2material()

    def _blender_set_material(self, material: Material):
        """
        Constructs material node, recreates color node if needed
        Args:
            material (Material): target material
        """
        object_material, bsdf_node = material.create_material()
        self._blender_material_node = object_material
        self._blender_bsdf_node = bsdf_node
        self._blender_object.active_material = object_material
        self._blender_create_colornode()

    def _blender_clear_material(self):
        """
        Clears Blender material node and nodes connected to it
        """
        if self._blender_material_node is not None:
            self._blender_colors_node.user_clear()
            self._blender_bsdf_node.user_clear()
            self._blender_material_node.user_clear()
            bpy.data.materials.remove(self._blender_material_node)
            self._blender_material_node = None
            self._blender_bsdf_node = None
            self._blender_colors_node = None

    def _blender_link_color2material(self):
        """
        Links color and material nodes
        """
        if self._blender_colors_node is not None and self._blender_material_node is not None:
            self._blender_material_node.node_tree.links.new(self._blender_bsdf_node.inputs['Base Color'],
                                                            self._blender_colors_node.outputs['Color'])

    def _blender_remove(self):
        """Removes the object from Blender scene"""
        self._blender_clear_colors()
        self._blender_clear_material()
        super()._blender_remove()

    def update_material(self, material: Material):
        """
        Updates object material properties, sets Blender structures accordingly
        Args:
            material (Material): target material
        """
        if self._blender_material_node is not None:
            self._blender_clear_material()
        self._blender_set_material(material)

    def update_colors(self, colors: Colors):
        """
        Updates object color properties, sets Blender structures accordingly
        Args:
            colors (Colors): target colors information
        """
        if self._blender_colors_node is not None:
            self._blender_clear_colors()
        self._blender_set_colors(colors)

