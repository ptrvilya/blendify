from abc import ABC, abstractmethod

import bpy

from .colors import Colors, UniformColors, VertexColors, TextureColors, FileTextureColors
from .materials import Material
from ..cameras import Camera
from ..internal.positionable import Positionable


class Renderable(Positionable):
    """
    Base class for all renderable objects (Meshes, PointClouds, Priimitives).
    """
    # ============================================== COLORSNODE BUILDERS ===============================================
    class ColorsNodeBuilder(ABC):
        colors_class = None

        def __init__(self, colors: Colors = None):
            self.has_alpha = False
            pass

        @abstractmethod
        def __call__(self, object_material: bpy.types.Material):
            return None

    class UniformColorsNodeBuilder(ColorsNodeBuilder):
        colors_class = UniformColors

        def __init__(self, colors: UniformColors):
            super().__init__()
            self.color = colors.color

    class VertexColorsNodeBuilder(ColorsNodeBuilder):
        colors_class = VertexColors

        def __init__(self, colors: VertexColors):
            super().__init__()
            self.has_alpha = colors.vertex_colors.shape[1] == 4

    class TextureColorsNodeBuilder(ColorsNodeBuilder):
        colors_class = TextureColors

        def __init__(self, colors: TextureColors):
            super().__init__()
            self.texture = colors.blender_texture

    class FileTextureColorsNodeBuilder(ColorsNodeBuilder):
        colors_class = FileTextureColors

        def __init__(self, colors: FileTextureColors):
            super().__init__()
            self.texture = colors.blender_texture
    # =========================================== END OF COLORSNODE BUILDERS ===========================================

    @abstractmethod
    def __init__(
        self,
        material: Material,
        colors: Colors,
        **kwargs
    ):
        """
        Creates internal structures, calls functions that connect Material and Colors to the object. Can only be called
        from child classes as the class is abstract.
        Args:
            material (Material): Material instance
            colors (Colors): Colors instance
            blender_object (bpy.types.Object): instance of Blender Object that is wrapped by the class
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        super().__init__(**kwargs)
        self._make_colorsnode_builders_dict()
        self.update_material(material)
        self.update_colors(colors)

    def _make_colorsnode_builders_dict(self):
        colorsnode_builders = {}
        for attrname in dir(self):
            attr = getattr(self, attrname)
            if isinstance(attr, type) and issubclass(attr, Renderable.ColorsNodeBuilder):
                if attr.colors_class is not None:
                    colorsnode_builders[attr.colors_class] = attr
        self._colorsnode_builders = colorsnode_builders

    def get_colorsnode_builder(self, colors: Colors):
        if isinstance(colors, tuple(self._colorsnode_builders.keys())):
            builder_class = self._colorsnode_builders[colors.__class__]
            builder = builder_class(colors)
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

    def update_camera(self, camera: Camera):
        """
        Updates object based on current camera position
        Args:
            camera (Camera): target camera
        """
        pass


class RenderableObject(Renderable):
    """
    Base class for renderable objects, that can be represented by a single bpy.types.Object (Meshes and Primitives).
    """
    # ============================================== COLORSNODE BUILDERS ===============================================
    class UniformColorsNodeBuilder(Renderable.UniformColorsNodeBuilder):
        def __call__(self, object_material: bpy.types.Material):
            color_node = object_material.node_tree.nodes.new('ShaderNodeRGB')
            color_node.outputs["Color"].default_value = self.color.tolist() + [1.]
            return color_node

    class VertexColorsNodeBuilder(Renderable.VertexColorsNodeBuilder):
        def __call__(self, object_material: bpy.types.Material):
            vertex_color_node = object_material.node_tree.nodes.new('ShaderNodeVertexColor')
            return vertex_color_node

    class TextureColorsNodeBuilder(Renderable.TextureColorsNodeBuilder):
        def __call__(self, object_material: bpy.types.Material):
            object_texture = object_material.node_tree.nodes.new('ShaderNodeTexImage')
            object_texture.image = self.texture
            return object_texture

    class FileTextureColorsNodeBuilder(Renderable.FileTextureColorsNodeBuilder):
        def __call__(self, object_material: bpy.types.Material):
            object_texture = object_material.node_tree.nodes.new('ShaderNodeTexImage')
            object_texture.image = self.texture
            return object_texture
    # =========================================== END OF COLORSNODE BUILDERS ===========================================

    @abstractmethod
    def __init__(
        self,
        **kwargs
    ):
        """
        Sets initial values for internal parameters, can only be called from child classes as the class is abstract.
        Args:
            material (Material): Material instance
            colors (Colors): Colors instance
            blender_object (bpy.types.Object): instance of Blender Object that is wrapped by the class
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        self._blender_colornode_builder = None
        self._blender_colors_node = None
        self._blender_material_node = None
        self._blender_bsdf_node = None
        super().__init__(**kwargs)

    @property
    def emit_shadows(self) -> bool:
        return self._blender_object.cycles_visibility.shadow

    @emit_shadows.setter
    def emit_shadows(self, val: bool):
        self._blender_object.cycles_visibility.shadow = val

    # ===================================================== OBJECT =====================================================
    @abstractmethod
    def _blender_create_object(self, *args, **kwargs):
        pass

    def _blender_remove_object(self):
        """Removes the object from Blender scene"""
        self._blender_clear_colors()
        self._blender_clear_material()
        super()._blender_remove_object()
    # ================================================== END OF OBJECT =================================================

    # ==================================================== MATERIAL ====================================================
    def update_material(self, material: Material):
        """
        Updates object material properties, sets Blender structures accordingly
        Args:
            material (Material): target material
        """
        if self._blender_material_node is not None:
            self._blender_clear_material()
        self._blender_set_material(material)

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
            if self._blender_colors_node is not None:
                self._blender_material_node.node_tree.nodes.remove(self._blender_colors_node)
                self._blender_colors_node = None
            self._blender_material_node.node_tree.nodes.remove(self._blender_bsdf_node)
            self._blender_material_node.user_clear()
            bpy.data.materials.remove(self._blender_material_node)
            self._blender_material_node = None
            self._blender_bsdf_node = None

    # ================================================ END OF MATERIAL =================================================

    # ===================================================== COLORS =====================================================
    def update_colors(self, colors: Colors):
        """
        Updates object color properties, sets Blender structures accordingly
        Args:
            colors (Colors): target colors information
        """
        if self._blender_colors_node is not None:
            self._blender_clear_colors()
        self._blender_set_colors(colors)

    def _blender_set_colors(self, colors: Colors):
        """
        Remembers current color properies, builds a color node for material
        Args:
            colors (Colors): target colors information
        """
        self._blender_colornode_builder = self.get_colorsnode_builder(colors)
        self._blender_create_colornode()

    def _blender_clear_colors(self):
        """
        Clears Blender color node and erases node constructor
        """
        if self._blender_colors_node is not None:
            self._blender_material_node.node_tree.nodes.remove(self._blender_colors_node)
            self._blender_colors_node = None
            self._blender_colornode_builder = None

    def _blender_create_colornode(self):
        """
        Creates color node using previously set builder
        """
        if self._blender_colornode_builder is not None and self._blender_material_node is not None:
            self._blender_colors_node = self._blender_colornode_builder(self._blender_material_node)
            self._blender_link_color2material()

    def _blender_link_color2material(self):
        """
        Links color and material nodes
        """
        if self._blender_colors_node is not None and self._blender_material_node is not None:
            if self._blender_bsdf_node.bl_label == "Principled BSDF":
                bsdf_color_input = "Base Color"
                if self._blender_colornode_builder.has_alpha:
                    self._blender_material_node.node_tree.links.new(self._blender_bsdf_node.inputs["Alpha"],
                                                                    self._blender_colors_node.outputs['Alpha'])
            elif self._blender_bsdf_node.bl_label == "Glossy BSDF":
                bsdf_color_input = "Color"
            else:
                raise RuntimeError(f"Unsupported material node: {self._blender_bsdf_node.bl_label}"
                                   f" in link_color2material")

            self._blender_material_node.node_tree.links.new(self._blender_bsdf_node.inputs[bsdf_color_input],
                                                            self._blender_colors_node.outputs['Color'])
            self._blender_bsdf_node.inputs[bsdf_color_input].default_value = [1.0, 0.0, 0.0, 1.0]
    # ================================================== END OF COLORS =================================================
