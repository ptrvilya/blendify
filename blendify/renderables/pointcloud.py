"""
MIT License

Copyright (c) 2018 Sebastian Bullinger
Copyright (c) 2021 Vladimir Guzov and Ilia Petrov

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import warnings
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

import bpy
import numpy as np
from mathutils import Vector

from .base import Renderable
from ..colors import VertexColors, UniformColors
from ..colors.base import ColorsMetadata, Colors
from ..internal.texture import compute_particle_color_texture
from ..materials.base import Material, MaterialInstance


@ dataclass
class ParticleMetadata:
    """Helper class that stores pointers to blender objects (colors, bsdf and material nodes),
    connected to each Particle System object
    """
    material_instance: Optional[MaterialInstance]  # Material instance for the particle system
    extra_color_nodes: Tuple[bpy.types.ShaderNode]  # Extra nodes in the material node tree necessary for proper color computation
    vertex_offset: int  # index of a starting vertex
    num_particles: int  # number of particles in particle collection
    texture_image: Optional[bpy.types.Image]  # texture image for per-vertex colors


class PointCloud(Renderable):
    """Basic point cloud consisting of vertices, supports uniform (UniformColors) and per-vertex (VertexColors) coloring.
    Uses Blender-Photogrammetry-Importer to handle point clouds as Blender particle systems objects

    Properties:
        emit_shadow (bool, optional): control whether particles representing the point cloud will emit shadow from
            any light source in the scene. This property may be turned off if the particle_emission_strength is big
            enough to avoid artifacts.
    """
    def __init__(
            self,
            vertices: np.ndarray,
            tag: str,
            point_size: float = 0.006,
            base_primitive: str = "CUBE",
            particle_emission_strength: int = 1,
            **kwargs
    ):
        """Creates Blender Collection that represent given point cloud. Code for creation particle systems for
        representing the point clouds is borrowed from https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer

        Args:
            vertices (np.ndarray): point cloud vertices
            material (Material): Material instance
            colors (Colors): VertexColors or UniformColors instance
            point_size (float, optional): size of a primitive, representing each vertex (default: 0.006)
            base_primitive (str, optional): type of primitive for representing each point
                (possible values are PLANE, CUBE, SPHERE, default: CUBE)
            particle_emission_strength (int, optional): strength of the emission from each primitive. This is used to
                increase realism. Values <= 0 turn emission off, values > 0 set the power of emission (default: 1)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: None (identity))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created collection in Blender
        """

        # internal variables and constants
        # This is a constraint imposed by open bug in blender https://developer.blender.org/T81103
        self._max_particles: int = 10000
        self._particle_collections = dict()
        self._point_size: float = point_size
        self._base_primitive: str = base_primitive.upper()
        self.particle_emission_strength: int = particle_emission_strength
        self._point_cloud_object_names: List[str] = list()
        self._particle_material_names: List[str] = list()

        self.num_vertices: int = 0
        self._particle_metadata: Dict[str, ParticleMetadata] = dict()  # particle_object_name: ParticleMetadata
        self._colors_metadata: Optional[ColorsMetadata] = None

        collection = self._blender_create_collection(vertices, tag)
        super().__init__(**kwargs, blender_object=collection, tag=tag)

    def update_vertices(
            self,
            vertices: np.ndarray
    ):
        """Updates pc vertices coordinates

        Args:
            vertices (np.ndarray): new coordinates for point cloud vertices
        """
        assert self.num_vertices == len(vertices), \
            f"Number of vertices should be the same (expected {self.num_vertices}, got {len(vertices)})"
        for subset_ind, offset in enumerate(range(0, self.num_vertices, self._max_particles)):
            points_subset = vertices[offset: offset + self._max_particles]

            # update PC object
            pc_object = self._blender_object.all_objects[f"Particle_{subset_ind}_PC"]
            for vert_ind, vert in enumerate(pc_object.vertices):
                vert.co = points_subset[vert_ind]
            pc_object.update()

    # Getter and setter for emit_shadow: this property may be turned off if the particle_emission_strength
    # is big enough to avoid artifacts.
    @property
    def emit_shadow(self):
        val = None
        for particle_obj_name in self._particle_metadata.keys():
            particle_obj = self._blender_object.all_objects[particle_obj_name]
            curr_val = particle_obj.cycles_visibility.shadow
            if val is None:
                val = curr_val
            elif val != curr_val:
                return None
        return val

    @emit_shadow.setter
    def emit_shadow(self, val: bool):
        for particle_obj_name in self._particle_metadata.keys():
            particle_obj = self._blender_object.all_objects[particle_obj_name]
            particle_obj.cycles_visibility.shadow = val

    # ===================================================== OBJECT =====================================================
    def _blender_create_collection(
            self,
            vertices: np.ndarray,
            tag: str
    ) -> bpy.types.Collection:
        """Creates Blender collection of particle systems, that represent point cloud

        Args:
            vertices (np.ndarray): all points in the point cloud
            tag (str): a name for a blender collection

        Returns:
            bpy.types.Collection: a collection of particle systems representing the point cloud
        """
        new_collection = bpy.data.collections.new(f"Particle System {tag}")
        bpy.context.collection.children.link(new_collection)

        self.point_cloud_obj_list = []
        self.num_vertices = len(vertices)
        for index, vertex_start in enumerate(range(0, self.num_vertices, self._max_particles)):
            # This name is used is a unique identifier for
            # the internal dictionary with metadata self._particle_metadata
            particle_obj_name = f"Particle_{index}"
            # particle_material_name = f"Particle_{index}_Material"
            point_cloud_obj_name = f"Particle_{index}_PC"

            self._point_cloud_object_names.append(point_cloud_obj_name)
            points_subset = vertices[vertex_start: vertex_start + self._max_particles]
            self._particle_metadata[particle_obj_name] = ParticleMetadata(
                material_instance=None,
                extra_color_nodes=tuple(),
                vertex_offset=vertex_start,
                num_particles=len(points_subset),
                texture_image=None
            )

            particle_obj = self._add_particle_obj(
                particle_obj_name=particle_obj_name,
                mesh_type=self._base_primitive,
                point_size=self._point_size,
                blender_collection=new_collection
            )
            point_cloud_obj = self._add_particle_system_obj(
                coords=points_subset,
                particle_obj=particle_obj,
                point_cloud_obj_name=point_cloud_obj_name,
                blender_collection=new_collection,
            )
            self.point_cloud_obj_list.append(point_cloud_obj)

        return new_collection

    def _blender_remove_object(self):
        """Removes the object from Blender scene
        """
        self._blender_clear_colors()
        self._blender_clear_material()
        super()._blender_remove_object()

    @staticmethod
    def _add_particle_obj(
            particle_obj_name: str,
            mesh_type: str,
            point_size: float,
            blender_collection: bpy.types.Collection
    ) -> bpy.types.Object:
        """Creates particle that will be used in particle system to represent vertices in the point cloud

        Args:
            particle_obj_name (str): name of a Blender primitive object to be created
            mesh_type (str): type of primitive for representing each point (possible values are PLANE, CUBE, SPHERE)
            point_size (float): size of a primitive
            blender_collection (bpy.types.Collection): a Blender collection for storing the primitive

        Returns:
            bpy.types.Object: a Blender primitive that is used to represent point cloud vertex
        """
        # The default size of elements added with
        #   primitive_cube_add, primitive_uv_sphere_add, etc. is (2,2,2)
        point_scale = point_size * 0.5
        bpy.ops.object.select_all(action="DESELECT")
        if mesh_type == "PLANE":
            bpy.ops.mesh.primitive_plane_add(size=point_scale)
        elif mesh_type == "CUBE":
            bpy.ops.mesh.primitive_cube_add(size=point_scale)
        elif mesh_type == "SPHERE":
            bpy.ops.mesh.primitive_uv_sphere_add(radius=point_scale)
        else:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=point_scale)
        particle_obj = bpy.context.object
        bpy.context.view_layer.objects.active = particle_obj
        bpy.ops.object.mode_set(mode='OBJECT')
        # Purposely repeating object name setting 2 times - for some primitives (cubes) setting it just ones sometimes doesn't work
        particle_obj.name = particle_obj_name
        particle_obj.name = particle_obj_name
        blender_collection.objects.link(particle_obj)
        bpy.context.collection.objects.unlink(particle_obj)

        return particle_obj

    @staticmethod
    def _add_particle_system_obj(
            coords: np.ndarray,
            particle_obj: bpy.types.Object,
            point_cloud_obj_name: str,
            blender_collection: bpy.types.Collection
    ) -> bpy.types.Object:
        """Creates particle system that represents a part of the point cloud (up to 10k vertices)
        using a given primitive

        Args:
            coords (np.ndarray): coordinates of point cloud vertices
            particle_obj (bpy.types.Object): a Blender primitive object that represents point cloud vertex
            point_cloud_obj_name (str): unique identifier of Blender particle system object tho be created
            blender_collection (bpy.types.Collection): a Blender collection for storing the particle system

        Returns:
            bpy.types.Object: Blender particle system object
        """
        point_cloud_mesh = bpy.data.meshes.new(point_cloud_obj_name)
        point_cloud_mesh.update()
        point_cloud_mesh.validate()
        point_cloud_mesh.from_pydata(coords, [], [])

        point_cloud_obj = bpy.data.objects.new(point_cloud_obj_name, point_cloud_mesh)
        blender_collection.objects.link(point_cloud_obj)
        point_cloud_obj.select_set(state=True)

        if bpy.context.view_layer.objects.active is None or bpy.context.view_layer.objects.active.mode == "OBJECT":
            bpy.context.view_layer.objects.active = point_cloud_obj

        if len(point_cloud_obj.particle_systems) == 0:
            point_cloud_obj.modifiers.new("particle sys", type="PARTICLE_SYSTEM")
            particle_sys = point_cloud_obj.particle_systems[0]
            settings = particle_sys.settings
            settings.type = "HAIR"
            settings.use_advanced_hair = True
            settings.emit_from = "VERT"
            settings.count = len(coords)
            # The final object extent is hair_length * obj.scale
            settings.hair_length = 100  # This must not be 0
            settings.use_emit_random = False
            settings.render_type = "OBJECT"
            settings.instance_object = particle_obj
            settings.use_rotations = True
            settings.rotation_mode = "GLOB_X"
        return point_cloud_obj
    # ================================================== END OF OBJECT =================================================

    # ==================================================== MATERIAL ====================================================
    def update_material(
            self,
            material: Material
    ):
        """Updates object material properties, sets Blender structures accordingly

        Args:
            material (Material): target material
        """
        if not isinstance(material, Material):
            assert len(material) == 1, "Only one material can be provided for the point cloud"
            material = material[0]
        self._blender_clear_material()
        self._blender_set_material(material)

    def _blender_set_material(
            self,
            material: Material
    ):
        """Constructs material node, recreates color node if needed

        Args:
            material (Material): target material
        """
        for particle_obj_name, metadata in self._particle_metadata.items():
            material_instance = material.create_material(name=f"{particle_obj_name}_Material")
            blender_material = material_instance.blender_material
            metadata.material_instance = material_instance
            particle_obj = self._blender_object.all_objects[particle_obj_name]
            particle_obj.data.materials.append(blender_material)

        self._blender_create_colors_node()
        self._blender_link_color2material()

    def _blender_clear_material(
            self,
    ):
        """Clears Blender material node and nodes connected to it
        """
        for particle_obj_name, metadata in self._particle_metadata.items():
            if metadata.material_instance is not None:
                material_instance = metadata.material_instance
                material_nodes = material_instance.blender_material.node_tree.nodes
                blender_material = material_instance.blender_material
                for material_node in material_nodes:
                    blender_material.node_tree.nodes.remove(material_node)
                particle_obj = self._blender_object.all_objects[particle_obj_name]
                particle_obj.data.materials.clear()
                blender_material.user_clear()
                bpy.data.materials.remove(blender_material)

                metadata.material_instance = None
                metadata.extra_color_nodes = tuple()

    # ================================================ END OF MATERIAL =================================================

    # ===================================================== COLORS =====================================================
    def update_colors(
            self,
            colors: Colors
    ):
        """Updates object color properties, sets Blender structures accordingly

        Args:
            colors (Colors): target colors information
        """
        if not isinstance(colors, Colors):
            assert len(colors) == 1, "Only one color can be provided for the point cloud"
            colors = colors[0]
        self._blender_clear_colors()
        self._blender_set_colors(colors)

    def _blender_set_colors(
            self,
            colors: Colors
    ):
        """Remembers current color properties, builds a color node for material

        Args:
            colors (Colors): target colors information
        """
        self._colors_metadata = colors.metadata

        # Create artificial textures if we have VertexColors
        if self._colors_metadata.type == VertexColors:
            for particle_obj_name, metadata in self._particle_metadata.items():
                vertex_offset = metadata.vertex_offset
                vertex_colors_subset = colors.vertex_colors[vertex_offset: vertex_offset + self._max_particles]
                metadata.texture_image = compute_particle_color_texture(vertex_colors_subset)

        self._blender_create_colors_node()
        self._blender_link_color2material()

    def _blender_clear_colors(
            self,
    ):
        """Clears Blender color node and erases node constructor
        """
        for particle_obj_name, metadata in self._particle_metadata.items():
            material_instance = metadata.material_instance
            if material_instance.colors_node is not None:
                blender_material = material_instance.blender_material
                blender_material.node_tree.nodes.remove(material_instance.colors_node)
                for extra_node in metadata.extra_color_nodes:
                    blender_material.node_tree.nodes.remove(extra_node)

                # Clear artificially created texture 
                if metadata.texture_image is not None:
                    # Remove only if the image has no users.
                    if not metadata.texture_image.users:
                        bpy.data.images.remove(metadata.texture_image)
                material_instance.colors_node = None
                metadata.extra_color_nodes = tuple()
                metadata.texture_image = None
                self._colors_metadata = None

    def _blender_create_colors_node(self):
        """Creates color node using previously set builder
        """
        if self._colors_metadata is not None:
            for particle_obj_name, metadata in self._particle_metadata.items():
                material_instance = metadata.material_instance
                blender_material = material_instance.blender_material

                if self._colors_metadata.type == UniformColors:
                    colors_node = blender_material.node_tree.nodes.new('ShaderNodeRGB')
                    colors_node.outputs[0].default_value = Vector(self._colors_metadata.color.tolist() + [1.]).to_4d()
                    material_instance.colors_node = colors_node
                elif self._colors_metadata.type == VertexColors:
                    particle_color_node = blender_material.node_tree.nodes.new("ShaderNodeTexImage")
                    particle_color_node.interpolation = "Closest"
                    particle_color_node.image = metadata.texture_image
                    particle_info_node = blender_material.node_tree.nodes.new("ShaderNodeParticleInfo")

                    # Idea: we use the particle idx to compute a texture coordinate
                    # Shift the un-normalized texture coordinate by a half pixel
                    shift_half_pixel_node = blender_material.node_tree.nodes.new("ShaderNodeMath")
                    shift_half_pixel_node.operation = "ADD"
                    blender_material.node_tree.links.new(
                        particle_info_node.outputs["Index"],
                        shift_half_pixel_node.inputs[0],
                    )
                    shift_half_pixel_node.inputs[1].default_value = 0.5

                    # Compute normalized texture coordinates (value between 0 and 1)
                    # by dividing by the number of particles
                    divide_node = blender_material.node_tree.nodes.new("ShaderNodeMath")
                    divide_node.operation = "DIVIDE"
                    blender_material.node_tree.links.new(
                        shift_half_pixel_node.outputs["Value"],
                        divide_node.inputs[0],
                    )
                    divide_node.inputs[1].default_value = metadata.num_particles

                    # Compute texture coordinate (x axis corresponds to particle idx)
                    shader_node_combine = blender_material.node_tree.nodes.new("ShaderNodeCombineXYZ")
                    blender_material.node_tree.links.new(
                        divide_node.outputs["Value"], shader_node_combine.inputs["X"]
                    )
                    blender_material.node_tree.links.new(
                        shader_node_combine.outputs["Vector"],
                        particle_color_node.inputs["Vector"],
                    )
                    material_instance.colors_node = particle_color_node
                    metadata.extra_color_nodes = (particle_info_node, shift_half_pixel_node, divide_node, shader_node_combine)
                else:
                    raise NotImplementedError(f"Unsupported colors class '{self._colors_metadata.type}'")

    def _blender_link_color2material(
            self
    ):
        """Links color and material nodes, additionally adds emission to particle color if needed
        """
        for particle_obj_name, metadata in self._particle_metadata.items():
            material_instance = metadata.material_instance
            if material_instance is not None:
                colors_node = material_instance.colors_node

                if colors_node is not None:
                    blender_material = material_instance.blender_material
                    colors_metadata = self._colors_metadata
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

                    if self.particle_emission_strength > 0:
                        if 'Emission' in material_instance.inputs:
                            blender_material.node_tree.links.new(
                                colors_node.outputs["Color"],
                                material_instance.inputs["Emission"],
                            )
                            material_instance.inputs["Emission Strength"].default_value = self.particle_emission_strength
                        else:
                            warnings.warn("This material does not support light emission; emission is ignored")

    # ================================================== END OF COLORS =================================================
