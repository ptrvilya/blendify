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
from typing import List, Union

import bpy
import numpy as np
from mathutils import Vector

from .base import Renderable
from .colors import Colors, VertexColors, UniformColors
from .materials import Material
from ..cameras import Camera
from ..internal.texture import _copy_values_to_image
from ..internal.types import Vector3d, Vector4d


class PointCloud(Renderable):
    """
    Basic point cloud consisting of vertices, supports uniform (UniformColors) and per-vertex (VertexColors) coloring.
    Uses Blender-Photogrammetry-Importer to handle point clouds as Blender particle systems objects.

    Properties:
        emit_shadow (bool, optional): control whether particles representing the point cloud will emit shadow from
            any light source in the scene. This property may be turned off if the particle_emission_strength is big
            enough to avoid artifacts.
    """
    # ============================================== COLORSNODE BUILDERS ===============================================
    class UniformColorsNodeBuilder(Renderable.UniformColorsNodeBuilder):
        def __call__(self, object_material: bpy.types.Material, **kwargs):
            color_node = object_material.node_tree.nodes.new('ShaderNodeRGB')
            rgba_vec = Vector(self.color.tolist() + [1.]).to_4d()
            color_node.outputs[0].default_value = rgba_vec
            return [color_node]

    class VertexColorsNodeBuilder(Renderable.VertexColorsNodeBuilder):
        def __init__(self, colors: VertexColors):
            # This is a constraint imposed by open bug in blender
            # https://developer.blender.org/T81103
            self._max_particles = 10000

            self.vertex_colors = colors.vertex_colors

        @staticmethod
        def _compute_particle_color_texture(colors, name="ParticleColor"):
            # To view the texture we set the height of the texture to vis_image_height
            image = bpy.data.images.new(name=name, width=len(colors), height=1)

            _copy_values_to_image(colors, image.name)
            image = bpy.data.images[image.name]
            # https://docs.blender.org/api/current/bpy.types.Image.html#bpy.types.Image.pack
            image.pack()
            return image

        def __call__(self, object_material: bpy.types.Material, vertex_offset: int, **kwargs):
            particle_color_node = object_material.node_tree.nodes.new("ShaderNodeTexImage")
            particle_color_node.interpolation = "Closest"
            vertex_colors_subset = self.vertex_colors[vertex_offset: vertex_offset + self._max_particles]
            particle_color_node.image = self._compute_particle_color_texture(vertex_colors_subset)
            particle_info_node = object_material.node_tree.nodes.new("ShaderNodeParticleInfo")

            # Idea: we use the particle idx to compute a texture coordinate
            # Shift the un-normalized texture coordinate by a half pixel
            shift_half_pixel_node = object_material.node_tree.nodes.new("ShaderNodeMath")
            shift_half_pixel_node.operation = "ADD"
            object_material.node_tree.links.new(
                particle_info_node.outputs["Index"],
                shift_half_pixel_node.inputs[0],
            )
            shift_half_pixel_node.inputs[1].default_value = 0.5

            # Compute normalized texture coordinates (value between 0 and 1)
            # by dividing by the number of particles
            divide_node = object_material.node_tree.nodes.new("ShaderNodeMath")
            divide_node.operation = "DIVIDE"
            object_material.node_tree.links.new(
                shift_half_pixel_node.outputs["Value"],
                divide_node.inputs[0],
            )
            divide_node.inputs[1].default_value = len(vertex_colors_subset)

            # Compute texture coordinate (x axis corresponds to particle idx)
            shader_node_combine = object_material.node_tree.nodes.new("ShaderNodeCombineXYZ")
            object_material.node_tree.links.new(
                divide_node.outputs["Value"], shader_node_combine.inputs["X"]
            )
            object_material.node_tree.links.new(
                shader_node_combine.outputs["Vector"],
                particle_color_node.inputs["Vector"],
            )

            return [particle_color_node, particle_info_node, shift_half_pixel_node, divide_node, shader_node_combine]
    # =========================================== END OF COLORSNODE BUILDERS ===========================================

    def __init__(
            self,
            vertices: np.ndarray,
            tag: str,
            point_size: float = 0.006,
            base_primitive: str = "CUBE",
            particle_emission_strength: int = 1,
            **kwargs
    ):
        """
        Creates Blender Collection that represent given point cloud. Code for creation particle systems for
        representing the point clouds is borrowed from https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer .
        Args:
            vertices (np.ndarray): point cloud vertices
            material (Material): PrinsipledBSDFMaterial instance
            colors (Colors): VertexColors or UniformColors instance
            point_size (float, optional): size of a primitive, represintg each vertex (default: 0.006)
            base_primitive (str, optional): type of primitive for representing each point
                (possible values are PLANE, CUBE, SPHERE, default: CUBE)
            particle_emission_strength (int, optional): strength of the emission from each primitive. This is used to
                increase realism. Values <= 0 turn emission off, values > 0 set the power of emission (default: 1)
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created collection in Blender
        """
        # TODO hasn't been tested with GlossyBSDFMaterial

        # internal variables and constants
        self._max_particles: int = 10000
        self._particle_collections = dict()
        self._point_size: float = point_size
        self._base_primitive: str = base_primitive
        self.particle_emission_strength: int = particle_emission_strength
        self._particle_object_names: List[str] = list()
        self._point_cloud_object_names: List[str] = list()
        self._particle_material_names: List[str] = list()

        self.num_vertices: int = 0
        self._blender_colornode_builder = None
        self._blender_colors_nodes = dict()    # particle_obj_name: [colors_node]
        self._blender_vertex_offsets = dict()  # particle_obj_name: index of a starting vertex
        self._blender_material_nodes = dict()  # particle_obj_name: material_node
        self._blender_bsdf_nodes = dict()      # particle_obj_name: bsdf_node

        collection = self._blender_create_collection(vertices, tag)
        super().__init__(**kwargs, blender_object=collection, tag=tag)

    def update_camera(
            self,
            camera: Camera
    ):
        """
        Updates object based on current camera position.
        Args:
            camera (Camera): target camera
        """
        pass

    def update_vertices(
            self,
            vertices: np.ndarray
    ):
        """
        Updates pc vertices corrdinates.
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
        for particle_obj_name in self._particle_object_names:
            particle_obj = self._blender_object.all_objects[particle_obj_name]
            curr_val = particle_obj.cycles_visibility.shadow
            if val is None:
                val = curr_val
            elif val != curr_val:
                return None
        return val

    @emit_shadow.setter
    def emit_shadow(self, val: bool):
        for particle_obj_name in self._particle_object_names:
            particle_obj = self._blender_object.all_objects[particle_obj_name]
            particle_obj.cycles_visibility.shadow = val

    # ===================================================== OBJECT =====================================================
    def _blender_create_collection(
            self,
            vertices: np.ndarray,
            tag: str
    ) -> bpy.types.Collection:
        """
        Creates Blender collection of particle systems, that represent point cloud.
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
            # This name is used is a unique identifier for all internal dictionaries (e.g. self._blender_colors_nodes)
            particle_obj_name = f"Particle_{index}"
            # particle_material_name = f"Particle_{index}_Material"
            point_cloud_obj_name = f"Particle_{index}_PC"

            self._particle_object_names.append(particle_obj_name)
            self._blender_colors_nodes[particle_obj_name] = None
            self._blender_material_nodes[particle_obj_name] = None
            self._point_cloud_object_names.append(point_cloud_obj_name)

            self._blender_vertex_offsets[particle_obj_name] = vertex_start
            points_subset = vertices[vertex_start: vertex_start + self._max_particles]

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
        """
        Removes the object from Blender scene.
        """
        for particle_obj_name, colors_nodes in self._blender_colors_nodes.items():
            if colors_nodes is not None:
                self._blender_clear_colors(particle_obj_name)
        for particle_obj_name, material_node in self._blender_material_nodes.items():
            if material_node is not None:
                self._blender_clear_material(particle_obj_name)
        super()._blender_remove_object()

    @staticmethod
    def _add_particle_obj(
            particle_obj_name: str,
            mesh_type: str,
            point_size: float,
            blender_collection: bpy.types.Collection
    ) -> bpy.types.Object:
        """
        Creates particle that will be used in particle system to represent vertices in the point cloud.
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
        """
        Creates particle system that represents a part of the point cloud (up to 10k vertices) using a given primitive.
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
        """
        Updates object material properties, sets Blender structures accordingly
        Args:
            material (Material): target material
        """
        for particle_obj_name, material_node in self._blender_material_nodes.items():
            if material_node is not None:
                self._blender_clear_material(particle_obj_name)
            self._blender_set_material(particle_obj_name, material)

    def _blender_set_material(
            self,
            particle_obj_name: str,
            material: Material
    ):
        """
        Constructs material node, recreates color node if needed
        Args:
            particle_obj_name (str): unique identifier of Blender particle system object that material is linked to
            material (Material): target material
        """
        object_material, bsdf_node = material.create_material(name=f"{particle_obj_name}_Material")

        node_tree = object_material.node_tree
        material_output_node = node_tree.nodes["Material Output"]
        node_tree.links.new(
            bsdf_node.outputs["BSDF"],
            material_output_node.inputs["Surface"],
        )

        self._blender_material_nodes[particle_obj_name] = object_material
        self._blender_bsdf_nodes[particle_obj_name] = bsdf_node

        particle_obj = self._blender_object.all_objects[particle_obj_name]
        particle_obj.data.materials.append(object_material)
        self._blender_create_colornode()

    def _blender_clear_material(
            self,
            particle_obj_name: str
    ):
        """
        Clears Blender material node and nodes connected to it
        Args:
            particle_obj_name (str): unique identifier of Blender particle system object that material is linked to
        """
        if self._blender_material_nodes[particle_obj_name] is not None:
            for color_node in self._blender_colors_nodes[particle_obj_name]:
                self._blender_material_nodes[particle_obj_name].node_tree.nodes.remove(color_node)
            self._blender_bsdf_nodes[particle_obj_name].user_clear()
            self._blender_material_nodes[particle_obj_name].user_clear()
            bpy.data.materials.remove(self._blender_material_nodes[particle_obj_name])
            self._blender_material_nodes[particle_obj_name] = None
            self._blender_bsdf_nodes[particle_obj_name] = None
            self._blender_colors_nodes[particle_obj_name] = None

    # ================================================ END OF MATERIAL =================================================

    # ===================================================== COLORS =====================================================
    def update_colors(
            self,
            colors: Colors
    ):
        """
        Updates object color properties, sets Blender structures accordingly
        Args:
            colors (Colors): target colors information
        """
        for particle_obj_name, colors_nodes in self._blender_colors_nodes.items():
            if colors_nodes is not None:
                self._blender_clear_colors(particle_obj_name)
        self._blender_set_colors(colors)

    def _blender_set_colors(
            self,
            colors: Colors
    ):
        """
        Remembers current color properies, builds a color node for material
        Args:
            colors (Colors): target colors information
        """
        self._blender_colornode_builder = self.get_colorsnode_builder(colors)
        self._blender_create_colornode()

    def _blender_clear_colors(
            self,
            particle_obj_name: str
    ):
        """
        Clears Blender color node and erases node constructor
        """
        if self._blender_colors_nodes[particle_obj_name] is not None:
            for color_node in self._blender_colors_nodes[particle_obj_name]:
                self._blender_material_nodes[particle_obj_name].node_tree.nodes.remove(color_node)
            self._blender_colors_nodes[particle_obj_name] = None
            self._blender_colornode_builder = None

    def _blender_create_colornode(self):
        """
        Creates color node using previously set builder
        """
        if self._blender_colornode_builder is not None:
            for particle_obj_name, colors_node in self._blender_colors_nodes.items():
                self._blender_colors_nodes[particle_obj_name] = \
                    self._blender_colornode_builder(self._blender_material_nodes[particle_obj_name],
                                                    self._blender_vertex_offsets[particle_obj_name])
                self._blender_link_color2material(particle_obj_name)

    def _blender_link_color2material(
            self,
            particle_obj_name: str
    ):
        """
        Links color and material nodes, additionally adds emission to particle color if needed
        """
        if self._blender_colors_nodes[particle_obj_name] is not None and \
                self._blender_material_nodes[particle_obj_name] is not None:
            # Add link for base color
            self._blender_material_nodes[particle_obj_name].node_tree.links.new(
                self._blender_colors_nodes[particle_obj_name][0].outputs["Color"],
                self._blender_bsdf_nodes[particle_obj_name].inputs["Base Color"],
            )

            # Add link for alpha to support transparency
            self._blender_material_nodes[particle_obj_name].node_tree.links.new(
                self._blender_colors_nodes[particle_obj_name][0].outputs["Alpha"],
                self._blender_bsdf_nodes[particle_obj_name].inputs["Alpha"],
            )

            # Add link for emission to improve color visibility and adjust emission strength
            if self.particle_emission_strength > 0:
                self._blender_material_nodes[particle_obj_name].node_tree.links.new(
                    self._blender_colors_nodes[particle_obj_name][0].outputs["Color"],
                    self._blender_bsdf_nodes[particle_obj_name].inputs["Emission"],
                )
                self._blender_bsdf_nodes[particle_obj_name].inputs["Emission Strength"].default_value = \
                    self.particle_emission_strength

    # ================================================== END OF COLORS =================================================


class CameraColoredPointCloud(PointCloud):
    """
        Special point cloud that colors only vertices that are visible from the camera, other vertices are colored
        to a solid pre-defined color. Supports uniform (UniformColors) and per-vertex (VertexColors) coloring.
        Uses Blender-Photogrammetry-Importer to handle point clouds.

        Properties:
        emit_shadow (bool, optional): control whether particles representing the point cloud will emit shadow from
            any light source in the scene. This property may be turned off if the particle_emission_strength is big
            enough to avoid artifacts.
    """

    def __init__(
            self,
            normals: np.ndarray,
            tag: str,
            back_color: Union[Vector3d, Vector4d] = (0.6, 0.6, 0.6),
            **kwargs
    ):
        """
        Creates Blender Collection that represent given point cloud. The class inherits most functionality from
        PointCloud and adds additional feature: provided per-vertex normals are used to recolor point cloud vertices
        that are not directly visible from the current camera (colors are updated after each camera change).
        Args:
            vertices (np.ndarray): point cloud vertices
            normals (np.ndarray): per-vertex normals for each point int the point cloud
            material (Material): PrinsipledBSDFMaterial object
            colors (Colors): VertexColors or UniformColors object
            point_size (float, optional): size of a primitive, represintg each vertex (default: 0.006)
            base_primitive (str, optional): type of primitive for representing each point
                (possible values are PLANE, CUBE, SPHERE, default: CUBE)
            particle_emission_strength (int, optional): strength of the emission from each primitive. This is used to
                increase realism. Values <= 0 turn emission off, values > 0 set the power of emission (default: 1)
            back_color (Union[Vector3d, Vector4d], optional): color for vertices that are not directly visible from
                current camera. Values are to be provided in [0.0, 1.0], alpha is optional (default: (0.6, 0.6, 0.6))
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            tag (str): name of the created collection in Blender
        """
        # Per point normals for each vertex. For example on how to estimate normals for PC refer to utils/pointcloud.py
        self.normals: np.ndarray = normals
        # Color for vertices that are not directly visible from current camera
        self.back_color: np.ndarray = np.array(back_color, dtype=np.float32)
        # We need to keep a local copy of initial per-vertex colors to recolor the PC in case of camera change
        self._per_vertex_colors: np.ndarray = None
        # We need to keep a local copy of the current camera ray to recolor the PC in case of colors change
        self._camera_ray: np.ndarray = None

        super().__init__(**kwargs, tag=tag)

    def update_vertices(
            self,
            vertices: np.ndarray,
            normals: np.ndarray
    ):
        """
        Updates point cloud vertices coordinates and normals, then recolors vertices according to new normals.
        Args:
            vertices (np.ndarray): new vertex coordinates
            normals (np.ndarray): new per-vertex normals
        """
        assert self.num_vertices == len(vertices), \
            f"Number of vertices should be the same (expected {self.num_vertices}, got {len(vertices)})"
        assert self.num_vertices == len(normals), \
            f"Number of vertices should be the same (expected {self.num_vertices}, got {len(normals)})"

        for subset_ind, offset in enumerate(range(0, self.num_vertices, self._max_particles)):
            points_subset = vertices[offset: offset + self._max_particles]

            # update PC object
            pc_object = self._blender_object.all_objects[f"Particle_{subset_ind}_PC"]
            for vert_ind, vert in enumerate(pc_object.vertices):
                vert.co = points_subset[vert_ind]
            pc_object.update()

            # Update normals and recolor PC
            self.normals = normals
            _per_vertex_colors_recolored = self._recompute_colors()
            self._update_colors_from_recolored(_per_vertex_colors_recolored)

    def update_colors(
            self,
            colors: Colors
    ):
        """
        Updates object color properties, sets Blender structures accordingly.
        Args:
            colors (Colors): target colors information
        """
        if isinstance(colors, UniformColors):
            self._per_vertex_colors = np.repeat(colors.color[np.newaxis], self.num_vertices, axis=0).astype(np.float32)
        elif isinstance(colors, VertexColors):
            self._per_vertex_colors = colors.vertex_colors.astype(np.float32)
        else:
            raise RuntimeError("Only Uniform and Vertex Colors are supported for CameraColoredPointCloud.")

        # Add alpha to support transparent back_color
        if self._per_vertex_colors.shape[1] == 3:
            alpha = np.ones((self._per_vertex_colors.shape[0], 1), dtype=np.float32)
            self._per_vertex_colors = np.concatenate((self._per_vertex_colors, alpha), axis=1)

        assert self.num_vertices == len(self._per_vertex_colors), \
            f"Number of colors should be the same as number of vertices(expected {self.num_vertices}, " \
            f"got {len(self._per_vertex_colors)})"

        if self._camera_ray is not None:
            _per_vertex_colors_recolored = self._recompute_colors()
            self._update_colors_from_recolored(_per_vertex_colors_recolored)
        else:
            self._update_colors_from_recolored(self._per_vertex_colors)

    def _update_colors_from_recolored(
            self,
            per_vertex_colors: np.ndarray
    ):
        """
        Creates internal VertexColors object with new colors and applies it to all particle systems.
        Args:
            per_vertex_colors (np.ndarray): new colors to apply to a point cloud
        """
        colors = VertexColors(per_vertex_colors)

        for particle_obj_name, colors_node in self._blender_colors_nodes.items():
            if colors_node is not None:
                self._blender_clear_colors(particle_obj_name)
        self._blender_set_colors(colors)

    def _recompute_colors(self):
        """
        Updates per-vertex colors based on angle between camera ray and normals. All invisible vertices are colored
        in self.back_color.
        Returns:
            np.ndarray: updated per-vertex colors
        """
        dot_product = (self.normals * self._camera_ray[None, :]).sum(axis=1)
        back_mask = dot_product > 0.0

        _per_vertex_colors_recolored = self._per_vertex_colors.copy()
        _per_vertex_colors_recolored[back_mask] = self.back_color[np.newaxis]

        return _per_vertex_colors_recolored

    def update_camera(
            self,
            camera: Camera
    ):
        """
        Updates object based on current camera position.
        Args:
            camera (Camera): target camera
        """
        self._camera_ray = camera.get_camera_ray()

        _per_vertex_colors_recolored = self._recompute_colors()
        self._update_colors_from_recolored(_per_vertex_colors_recolored)
