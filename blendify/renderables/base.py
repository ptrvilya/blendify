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
    def __init__(self, material: Material, colors: Colors, tag: str, blender_object: bpy_types.Object):
        super().__init__(tag, blender_object)
        self._blender_colors_node = None
        self._blender_material_node = None
        self._blender_bsdf_node = None
        self.update_material(material)
        self.update_colors(colors)

    def update_camera(self, camera: Camera):
        pass

    @abstractmethod
    def _blender_clear_colors(self):
        if self._blender_colors_node is not None:
            self._blender_colors_node.user_clear()
            #TODO: finish the colors desctructor

    @abstractmethod
    def _blender_set_colors(self, colors: Colors):
        color_node = colors.create_blender_colornode(self._blender_material_node)
        self._blender_colors_node = color_node
        self._blender_link_color2material()

    def _blender_set_material(self, material: Material):
        object_material, bsdf_node = material.create_material()
        self._blender_material_node = object_material
        self._blender_bsdf_node = bsdf_node
        self._blender_object.active_material = object_material
        self._blender_link_color2material()

    def _blender_clear_material(self):
        if self._blender_material_node is not None:
            self._blender_material_node.user_clear()
            bpy.data.materials.remove(self._blender_material_node)
            self._blender_material_node = None
            self._blender_bsdf_node = None

    def _blender_link_color2material(self):
        if self._blender_colors_node is not None and self._blender_material_node is not None:
            self._blender_material_node.node_tree.links.new(self._blender_bsdf_node.inputs['Base Color'],
                                                            self._blender_colors_node.outputs['Color'])



    def update_material(self, material: Material):
        if self._blender_material_node is not None:
            self._blender_clear_material()
        self._blender_set_material(material)

    def update_colors(self, colors: Colors):
        if self._blender_colors_node is not None:
            self._blender_clear_colors()
        self._blender_set_colors(colors)

