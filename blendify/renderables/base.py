from abc import abstractmethod
from typing import Optional, List, Union

import bpy
import warnings

from ..colors import UniformColors, VertexColors
from ..colors.base import ColorsMetadata, ColorsList, Colors
from ..colors.texture import TextureColors, FileTextureColors
from ..internal.positionable import Positionable
from ..materials.base import MaterialList, MaterialInstance, Material


class Renderable(Positionable):
    """
    Base class for all renderable objects (Meshes, PointClouds, Primitives).
    """

    @abstractmethod
    def __init__(
            self,
            material: Union[Material, MaterialList],
            colors: Union[Colors, ColorsList],
            **kwargs
    ):
        """Creates internal structures, calls functions that connect Material and Colors to the object.
        Can only be called from child classes as the class is abstract.

        Args:
            material (Union[Material, MaterialList]): Material instance or a list of Material instances
            colors (Union[Colors, ColorsList]): Colors instance or a list of Colors instances
            blender_object (bpy.types.Object): instance of Blender Object that is wrapped by the class
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: None (identity))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        super().__init__(**kwargs)
        self._materials_count = len(material) if not isinstance(material, Material) else 1
        self.update_material(material)
        self.update_colors(colors)

    def update_material(self, material: Union[Material, MaterialList]):
        """Updates object material properties, sets Blender structures accordingly
        Args:
            material (Union[Material, MaterialList]): target material or a list of target materials
        """
        pass

    def update_colors(self, colors: Union[Colors, ColorsList]):
        """Updates object color properties, sets Blender structures accordingly

        Args:
            colors (Union[Colors, ColorsList]): target colors information or a list of target colors information
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
            material (MaterialList): Material instance or a list of Material instances
            colors (ColorsList): Colors instance or a list of Colors instances
            blender_object (bpy.types.Object): instance of Blender Object that is wrapped by the class
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: None (identity))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created object in Blender
        """
        self._material_instances: Optional[List[MaterialInstance]] = None
        self._colors_metadatas: Optional[List[ColorsMetadata]] = None
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
        self._blender_clear_materials()
        super()._blender_remove_object()

    # ================================================== END OF OBJECT =================================================

    # ==================================================== MATERIAL ====================================================
    def update_material(self, material: Union[Material, MaterialList]):
        """Updates object material properties, sets Blender structures accordingly

        Args:
            material (Union[Material, MaterialList]): target material or a list of target materials
        """
        if self._material_instances is not None:
            self._blender_clear_materials()

        # Turn single material into a list
        if isinstance(material, Material):
            material_list = [material]
        else:
            material_list = material

        self._blender_set_materials(material_list)

    def _blender_assign_materials(self):
        """Assigns created materials to the object"""
        blender_material = self._material_instances[0].blender_material
        self._blender_object.active_material = blender_material

    def _blender_set_materials(self, material_list: MaterialList):
        """Constructs material node, recreates color node if needed

        Args:
            material_list (MaterialList): list of target materials
        """
        assert len(material_list) > 0, "Material list must contain at least one material"
        assert len(material_list) == self._materials_count, "Material list must contain the same number of elements as during object creation"

        self._material_instances = []

        for material in material_list:
            material_instance = material.create_material()
            self._blender_object.data.materials.append(material_instance.blender_material)
            self._material_instances.append(material_instance)
        self._blender_create_colors_nodes()
        self._blender_link_color2material()
        self._blender_assign_materials()

    def _blender_clear_materials(self):
        """Clears Blender material node and nodes connected to it
        """
        if self._material_instances is not None:
            self._blender_object.active_material = None
            for material_instance in self._material_instances:
                material_nodes = material_instance.blender_material.node_tree.nodes
                blender_material = material_instance.blender_material
                for material_node in material_nodes:
                    blender_material.node_tree.nodes.remove(material_node)
                blender_material.user_clear()
                bpy.data.materials.remove(blender_material)
            self._material_instances = None

    # ================================================ END OF MATERIAL =================================================

    # ===================================================== COLORS =====================================================
    def update_colors(self, colors: Union[Colors, ColorsList]):
        """Updates object color properties, sets Blender structures accordingly

        Args:
            colors (Colors): target colors information
        """
        if self._material_instances is not None:
            self._blender_clear_colors()

        # Turn single colors into a list
        if isinstance(colors, Colors):
            colors_list = [colors]
        else:
            colors_list = colors
        self._blender_set_colors(colors_list)

    def _blender_set_colors(self, colors_list: ColorsList):
        """Remembers current color properties, builds a color node for material (from colors_metadata)
        """
        assert len(colors_list) > 0, "Colors list must contain at least one color"
        assert len(colors_list) == self._materials_count, "Colors list must contain the same number of elements as materials"

        self._colors_metadatas = []
        for material_ind, colors in enumerate(colors_list):
            self._colors_metadatas.append(colors.metadata)
        self._blender_create_colors_nodes()
        self._blender_link_color2material()

    def _blender_clear_colors(self):
        """Clears Blender color node and erases node constructor
        """
        if self._material_instances is not None and self._colors_metadatas is not None:
            for material_instance, colors_metadata in zip(self._material_instances, self._colors_metadatas):
                if colors_metadata.type is UniformColors and colors_metadata.has_alpha:
                    # return the alpha channel back to the default value
                    material_instance.inputs['Alpha'].default_value = 1.
                blender_material = material_instance.blender_material
                blender_material.node_tree.nodes.remove(material_instance.colors_node)
                material_instance.colors_node = None
        self._colors_metadatas = None

    def _blender_create_colors_nodes(self):
        """Creates color node using previously set builder
        """
        if self._colors_metadatas is not None and self._material_instances is not None:
            for material_instance, colors_metadata in zip(self._material_instances, self._colors_metadatas):
                blender_material = material_instance.blender_material
                if colors_metadata.type is UniformColors:
                    colors_node = blender_material.node_tree.nodes.new('ShaderNodeRGB')
                    if colors_metadata.has_alpha:
                        colors_node.outputs["Color"].default_value = colors_metadata.color.tolist()
                    else:
                        colors_node.outputs["Color"].default_value = colors_metadata.color.tolist() + [1.]  # add alpha 1.0
                elif colors_metadata.type is VertexColors:
                    colors_node = blender_material.node_tree.nodes.new('ShaderNodeVertexColor')
                elif colors_metadata.type is TextureColors:
                    colors_node = blender_material.node_tree.nodes.new('ShaderNodeTexImage')
                    colors_node.image = colors_metadata.texture
                elif colors_metadata.type is FileTextureColors:
                    colors_node = blender_material.node_tree.nodes.new('ShaderNodeTexImage')
                    colors_node.image = colors_metadata.texture
                else:
                    raise NotImplementedError(f"Unsupported colors class '{colors_metadata.type}'")
                material_instance.colors_node = colors_node

    def _blender_link_color2material(self):
        """Links color and material nodes
        """
        if self._material_instances is not None and self._colors_metadatas is not None:
            for material_instance, colors_metadata in zip(self._material_instances, self._colors_metadatas):
                if material_instance.colors_node is not None:
                    blender_material = material_instance.blender_material
                    blender_material.node_tree.links.new(material_instance.inputs['Color'],
                                                         material_instance.colors_node.outputs['Color'])
                    material_instance.inputs['Color'].default_value = [1.0, 0.0, 0.0, 1.0]
                    if colors_metadata.has_alpha:
                        if 'Alpha' in material_instance.inputs:
                            if colors_metadata.type is UniformColors:
                                material_instance.inputs['Alpha'].default_value = colors_metadata.color[3]
                            else:
                                blender_material.node_tree.links.new(material_instance.inputs['Alpha'],
                                                                     material_instance.colors_node.outputs['Alpha'])
                        else:
                            warnings.warn("This material does not support transparency; alpha color channel is ignored")
    # ================================================== END OF COLORS =================================================
