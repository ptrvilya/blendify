import numpy as np
import bpy_types
import bpy
from typing import Union, Tuple, List, Sequence
from abc import ABC, abstractmethod
from ..cameras import Camera
from .colors import Colors
from .materials import Material
from ..internal.positionable import Positionable


class Renderable(Positionable):
    @abstractmethod
    def __init__(self, material: Material, colors: Colors, tag: str, blender_object: bpy_types.Object):
        super().__init__(tag, blender_object)
        self._blender_colornode_builder = None
        self._blender_colors_node = None
        self._blender_material_node = None
        self._blender_bsdf_node = None
        self.update_material(material)
        self.update_colors(colors)

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
        self._blender_colornode_builder = colors.get_colornode_builder()
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

