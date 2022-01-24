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
import numpy as np
import bpy_types
import bpy
from mathutils import Vector
from typing import Union, Tuple, List, Sequence
from ..cameras import Camera
from .colors import Colors, VertexColors
from .materials import Material
from .base import Renderable
from ..internal.types import Vector3d, Vector4d


class PC(Renderable):
    """
    Basic PC with vertices, supports uniform and per-vertex coloring.
    Uses Blender-Photogrammetry-Importer to handle PCs.
    """

    class UniformColorsNodeBuilder(Renderable.UniformColorsNodeBuilder):
        def __call__(self, object_material: bpy.types.Material, **kwargs):
            color_node = object_material.node_tree.nodes.new('ShaderNodeRGB')
            rgba_vec = Vector(self.color.tolist() + [1.]).to_4d()
            color_node.outputs[0].default_value = rgba_vec
            return color_node

    class VertexColorsNodeBuilder(Renderable.VertexColorsNodeBuilder):
        def __init__(self, colors: VertexColors):
            self._max_particles = 10000

            self.vertex_colors = colors.vertex_colors

        @staticmethod
        def _copy_values_to_image(value_tripplets, image_name):
            """ Copy values to image pixels. """
            image = bpy.data.images[image_name]
            # working on a copy of the pixels results in a MASSIVE performance speed
            local_pixels = list(image.pixels[:])
            for value_index, tripplet in enumerate(value_tripplets):
                column_offset = value_index * 4  # (R,G,B,A)
                # Order is R,G,B, opacity
                local_pixels[column_offset] = tripplet[0]
                local_pixels[column_offset + 1] = tripplet[1]
                local_pixels[column_offset + 2] = tripplet[2]
                # opacity (0 = transparent, 1 = opaque)
                # local_pixels[column_offset + 3] = 1.0    # already set by default
            image.pixels = local_pixels[:]

        @staticmethod
        def _compute_particle_color_texture(colors, name="ParticleColor"):
            # To view the texture we set the height of the texture to vis_image_height
            image = bpy.data.images.new(name=name, width=len(colors), height=1)

            PC.VertexColorsNodeBuilder._copy_values_to_image(colors, image.name)
            image = bpy.data.images[image.name]
            # https://docs.blender.org/api/current/bpy.types.Image.html#bpy.types.Image.pack
            image.pack()
            return image

        def __call__(self, object_material: bpy.types.Material, vertex_index: int, **kwargs):
            particle_color_node = object_material.node_tree.nodes.new("ShaderNodeTexImage")
            particle_color_node.interpolation = "Closest"
            vertex_colors_subset = self.vertex_colors[vertex_index: vertex_index + self._max_particles]
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

            return particle_color_node

    def __init__(self, vertices: np.ndarray, material: Material, colors: Colors, tag: str,
            point_size: float = 0.006, base_primitive: str = "CUBE", add_particle_color_emission: bool = True,
            quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0)):
        # internal variables and constants
        self._max_particles = 10000
        self._particle_collections = {}
        self._point_size = point_size
        self._base_primitive = base_primitive
        self.add_particle_color_emission = add_particle_color_emission
        self._particle_object_names: List[str] = list()
        self._point_cloud_object_names: List[str] = list()
        self._particle_material_names: List[str] = list()

        self.num_vertices = 0
        self._blender_colornode_builder = None
        self._blender_colors_nodes = dict()  # particle_obj_name: colors_node
        self._blender_material_nodes = dict()  # particle_obj_name: material_node
        self._blender_bsdf_nodes = dict()  # particle_obj_name: bsdf_node

        collection = self._blender_create_collection(vertices, tag)
        super().__init__(material, colors, tag, collection, quaternion, translation)

    def update_camera(self, camera: Camera):
        """
        Updates object based on current camera position
        Args:
            camera (Camera): target camera
        """
        pass

    def update_vertices(self, vertices: np.ndarray):
        """
        Updates mesh vertices corrdinates
        Args:
            vertices: new vertex coordinates
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

    # ===> OBJECT
    def _blender_create_collection(self, vertices: np.ndarray, tag: str):
        new_collection = bpy.data.collections.new(f"Particle System {tag}")
        bpy.context.collection.children.link(new_collection)

        self.point_cloud_obj_list = []
        self.num_vertices = len(vertices)
        for i in range(0, self.num_vertices, self._max_particles):
            particle_obj_name = f"Particle_{i}"
            # particle_material_name = f"Particle_{i}_Material"
            point_cloud_obj_name = f"Particle_{i}_PC"

            self._particle_object_names.append(particle_obj_name)
            self._blender_colors_nodes[particle_obj_name] = None
            self._blender_material_nodes[particle_obj_name] = None
            self._point_cloud_object_names.append(point_cloud_obj_name)

            points_subset = vertices[i: i + self._max_particles]

            particle_obj = self._add_particle_obj(
                particle_obj_name,
                mesh_type=self._base_primitive,
                point_extent=self._point_size,
                reconstruction_collection=new_collection
            )
            point_cloud_obj = self._add_particle_system_obj(
                points_subset,
                particle_obj,
                point_cloud_obj_name,
                new_collection,
            )
            self.point_cloud_obj_list.append(point_cloud_obj)

        return new_collection

    def _blender_remove_object(self):
        """Removes the object from Blender scene"""
        for particle_obj_name, colors_node in self._blender_colors_nodes.items():
            if colors_node is not None:
                self._blender_clear_colors(particle_obj_name)
        for particle_obj_name, material_node in self._blender_material_nodes.items():
            if material_node is not None:
                self._blender_clear_material(particle_obj_name)
        super()._blender_remove_object()

    @staticmethod
    def _add_particle_obj(particle_obj_name, mesh_type, point_extent, reconstruction_collection):
        # The default size of elements added with
        #   primitive_cube_add, primitive_uv_sphere_add, etc. is (2,2,2)
        point_scale = point_extent * 0.5

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
        reconstruction_collection.objects.link(particle_obj)
        bpy.context.collection.objects.unlink(particle_obj)

        return particle_obj

    @staticmethod
    def _add_particle_system_obj(coords, particle_obj, point_cloud_obj_name, reconstruction_collection):
        point_cloud_mesh = bpy.data.meshes.new(point_cloud_obj_name)
        point_cloud_mesh.update()
        point_cloud_mesh.validate()
        point_cloud_mesh.from_pydata(coords, [], [])

        point_cloud_obj = bpy.data.objects.new(point_cloud_obj_name, point_cloud_mesh)
        reconstruction_collection.objects.link(point_cloud_obj)
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
        return point_cloud_obj

    # <=== OBJECT

    # ===> MATERIAL
    def update_material(self, material: Material):
        """
        Updates object material properties, sets Blender structures accordingly
        Args:
            material (Material): target material
        """
        for particle_obj_name, material_node in self._blender_material_nodes.items():
            if material_node is not None:
                self._blender_clear_material(particle_obj_name)
            self._blender_set_material(particle_obj_name, material)

    def _blender_set_material(self, particle_obj_name: str, material: Material):
        """
        Constructs material node, recreates color node if needed
        Args:
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

    def _blender_clear_material(self, particle_obj_name: str):
        """
        Clears Blender material node and nodes connected to it
        """
        if self._blender_material_nodes[particle_obj_name] is not None:
            self._blender_colors_nodes[particle_obj_name].user_clear()
            self._blender_bsdf_nodes[particle_obj_name].user_clear()
            self._blender_material_nodes[particle_obj_name].user_clear()
            bpy.data.materials.remove(self._blender_material_nodes[particle_obj_name])
            self._blender_material_nodes[particle_obj_name] = None
            self._blender_bsdf_nodes[particle_obj_name] = None
            self._blender_colors_nodes[particle_obj_name] = None

    # <=== MATERIAL

    # ===> COLORS
    def update_colors(self, colors: Colors):
        """
        Updates object color properties, sets Blender structures accordingly
        Args:
            colors (Colors): target colors information
        """
        for particle_obj_name, colors_node in self._blender_colors_nodes.items():
            if colors_node is not None:
                self._blender_clear_colors(particle_obj_name)
        self._blender_set_colors(colors)

    def _blender_set_colors(self, colors: Colors):
        """
        Remembers current color properies, builds a color node for material
        Args:
            colors (Colors): target colors information
        """
        self._blender_colornode_builder = self.get_colorsnode_builder(colors)
        self._blender_create_colornode()

    def _blender_clear_colors(self, particle_obj_name: str):
        """
        Clears Blender color node and erases node constructor
        """
        if self._blender_colors_nodes[particle_obj_name] is not None:
            self._blender_colors_nodes[particle_obj_name].user_clear()
            self._blender_colors_nodes[particle_obj_name] = None
            self._blender_colornode_builder = None

    def _blender_create_colornode(self):
        """
        Creates color node using previously set builder
        """
        if self._blender_colornode_builder is not None:
            for particle_obj_name, colors_node in self._blender_colors_nodes.items():
                self._blender_colors_nodes[particle_obj_name] = \
                    self._blender_colornode_builder(self._blender_material_nodes[particle_obj_name])
                self._blender_link_color2material(particle_obj_name)

    def _blender_link_color2material(self, particle_obj_name: str):
        """
        Links color and material nodes
        """
        if self._blender_colors_nodes[particle_obj_name] is not None and \
                self._blender_material_nodes[particle_obj_name] is not None:
            # Add links for base color and emission to improve color visibility
            self._blender_material_nodes[particle_obj_name].node_tree.links.new(
                self._blender_colors_nodes[particle_obj_name].outputs["Color"],
                self._blender_bsdf_nodes[particle_obj_name].inputs["Base Color"],
            )

            if self.add_particle_color_emission:
                self._blender_material_nodes[particle_obj_name].node_tree.links.new(
                    self._blender_colors_nodes[particle_obj_name].outputs["Color"],
                    self._blender_bsdf_nodes[particle_obj_name].inputs["Emission"],
                )
    # <=== COLORS
