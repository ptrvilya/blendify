from abc import abstractmethod
from typing import Optional

import bpy

from ..colors import UniformColors, VertexColors
from ..colors.base import ColorsMetadata, Colors
from ..colors.texture import TextureColors, FileTextureColors
from ..internal.positionable import Positionable
from ..materials.base import Material


class Renderable(Positionable):
    """
    Base class for all renderable objects (Meshes, PointClouds, Primitives).
    """

    @abstractmethod
    def __init__(
            self,
            material: Material,
            colors: Colors,
            **kwargs
    ):
        """Creates internal structures, calls functions that connect Material and Colors to the object.
        Can only be called from child classes as the class is abstract.

        Args:
            material (Material): Material instance
            colors (Colors): Colors instance
            blender_object (bpy.types.Object): instance of Blender Object that is wrapped by the class
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        super().__init__(**kwargs)
        self.update_material(material)
        self.update_colors(colors)

    def update_material(self, material: Material):
        """Updates object material properties, sets Blender structures accordingly
        Args:
            material (Material): target material
        """
        pass

    def update_colors(self, colors: Colors):
        """Updates object color properties, sets Blender structures accordingly

        Args:
            colors (Colors): target colors information
        """
        pass


class RenderableObject(Renderable):
    """
    Base class for renderable objects, that can be represented by a single bpy.types.Object (Meshes and Primitives).
    """

    @abstractmethod
    def __init__(
            self,
            **kwargs
    ):
        """Sets initial values for internal parameters, can only be called from child classes as the class is abstract.

        Args:
            material (Material): Material instance
            colors (Colors): Colors instance
            blender_object (bpy.types.Object): instance of Blender Object that is wrapped by the class
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        self._blender_colors_node = None
        self._blender_material_node = None
        self._blender_bsdf_node = None
        self._colors_metadata: Optional[ColorsMetadata] = None
        super().__init__(**kwargs)

    @property
    def emit_shadows(self) -> bool:
        return self._blender_object.visible_shadow

    @emit_shadows.setter
    def emit_shadows(self, val: bool):
        self._blender_object.visible_shadow = val

    # ===================================================== OBJECT =====================================================
    @abstractmethod
    def _blender_create_object(self, *args, **kwargs):
        pass

    def _blender_remove_object(self):
        """Removes the object from Blender scene
        """
        self._blender_clear_colors()
        self._blender_clear_material()
        super()._blender_remove_object()

    # ================================================== END OF OBJECT =================================================

    # ==================================================== MATERIAL ====================================================
    def update_material(self, material: Material):
        """Updates object material properties, sets Blender structures accordingly

        Args:
            material (Material): target material
        """
        if self._blender_material_node is not None:
            self._blender_clear_material()
        self._blender_set_material(material)

    def _blender_set_material(self, material: Material):
        """Constructs material node, recreates color node if needed

        Args:
            material (Material): target material
        """
        object_material, bsdf_node = material.create_material()
        self._blender_material_node = object_material
        self._blender_bsdf_node = bsdf_node
        self._blender_object.active_material = object_material
        self._blender_create_colors_node()
        self._blender_link_color2material()

    def _blender_clear_material(self):
        """Clears Blender material node and nodes connected to it
        """
        if self._blender_material_node is not None:
            if self._blender_colors_node is not None:
                self._blender_material_node.node_tree.nodes.remove(self._blender_colors_node)
                self._blender_colors_node = None
            self._blender_material_node.node_tree.nodes.remove(self._blender_bsdf_node)
            self._blender_object.active_material = None
            self._blender_material_node.user_clear()
            bpy.data.materials.remove(self._blender_material_node)
            self._blender_material_node = None
            self._blender_bsdf_node = None

    # ================================================ END OF MATERIAL =================================================

    # ===================================================== COLORS =====================================================
    def update_colors(self, colors: Colors):
        """Updates object color properties, sets Blender structures accordingly

        Args:
            colors (Colors): target colors information
        """
        if self._blender_colors_node is not None:
            self._blender_clear_colors()
        self._blender_set_colors(colors)

    def _blender_set_colors(self, colors: Colors):
        """Remembers current color properties, builds a color node for material (from colors_metadata)
        """
        self._colors_metadata = colors.metadata

        self._blender_create_colors_node()
        self._blender_link_color2material()

    def _blender_clear_colors(self):
        """Clears Blender color node and erases node constructor
        """
        if self._blender_colors_node is not None:
            if self._colors_metadata.type is UniformColors and self._colors_metadata.has_alpha:
                # return the alpha channel back to the default value
                self._blender_bsdf_node.inputs['Alpha'].default_value = 1.
            self._blender_material_node.node_tree.nodes.remove(self._blender_colors_node)
            self._blender_colors_node = None
            self._colors_metadata = None

    def _blender_create_colors_node(self):
        """Creates color node using previously set builder
        """
        if self._colors_metadata is not None and self._blender_material_node is not None:
            material_node = self._blender_material_node

            if self._colors_metadata.type is UniformColors:
                colors_node = material_node.node_tree.nodes.new('ShaderNodeRGB')
                if self._colors_metadata.has_alpha:
                    colors_node.outputs["Color"].default_value = self._colors_metadata.color.tolist()
                else:
                    colors_node.outputs["Color"].default_value = self._colors_metadata.color.tolist() + [1.]  # add alpha 1.0
            elif self._colors_metadata.type is VertexColors:
                colors_node = material_node.node_tree.nodes.new('ShaderNodeVertexColor')
            elif self._colors_metadata.type is TextureColors:
                colors_node = material_node.node_tree.nodes.new('ShaderNodeTexImage')
                colors_node.image = self._colors_metadata.texture
            elif self._colors_metadata.type is FileTextureColors:
                colors_node = material_node.node_tree.nodes.new('ShaderNodeTexImage')
                colors_node.image = self._colors_metadata.texture
            else:
                raise NotImplementedError(f"Unsupported colors class '{self._colors_metadata.type}'")
            self._blender_colors_node = colors_node

    def _blender_link_color2material(self):
        """Links color and material nodes
        """
        if self._blender_colors_node is not None and self._blender_material_node is not None:
            if self._blender_bsdf_node.bl_label == "Principled BSDF":
                bsdf_color_input = "Base Color"
                if self._colors_metadata.has_alpha:
                    if self._colors_metadata.type is UniformColors:
                        self._blender_bsdf_node.inputs['Alpha'].default_value = self._colors_metadata.color[3]
                    else:
                        self._blender_material_node.node_tree.links.new(self._blender_bsdf_node.inputs["Alpha"],
                                                                        self._blender_colors_node.outputs['Alpha'])
            elif self._blender_bsdf_node.bl_label == "Glossy BSDF":
                bsdf_color_input = "Color"
            else:
                raise NotImplementedError(f"Unsupported material node: {self._blender_bsdf_node.bl_label}"
                                          f" in link_color2material")

            self._blender_material_node.node_tree.links.new(self._blender_bsdf_node.inputs[bsdf_color_input],
                                                            self._blender_colors_node.outputs['Color'])
            self._blender_bsdf_node.inputs[bsdf_color_input].default_value = [1.0, 0.0, 0.0, 1.0]
    # ================================================== END OF COLORS =================================================
