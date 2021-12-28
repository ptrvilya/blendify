from typing import Union
from pathlib import Path

import bpy

from .lights import LightsCollection
from .renderables import RenderablesCollection
from .internal import Singleton
from .cameras import Camera


class Scene(metaclass=Singleton):
    def __init__(self):
        # Initialise Blender scene
        self._set_default_blender_scene()

        self.renderables = RenderablesCollection()
        self.lights = LightsCollection()
        self._camera = None

    @staticmethod
    def _set_default_blender_scene():
        # TODO inspect all lines (maybe add something)
        # Setup scene parameters
        scene = bpy.data.scenes[0]
        scene.use_nodes = True
        bpy.context.scene.world.use_nodes = False
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.render.image_settings.color_mode = 'RGBA'
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.image_settings.quality = 100
        bpy.context.scene.world.color = (0, 0, 0)
        bpy.context.scene.render.film_transparent = True
        bpy.context.scene.cycles.filter_width = 0  # turn off anti-aliasing
        # Important if you want to get a pure color background (eg. white background)
        bpy.context.scene.view_settings.view_transform = 'Raw'
        bpy.context.scene.cycles.samples = 128  # Default value, can be changed in .render
        # Empty the scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

    @property
    def camera(self) -> Camera:
        return self._camera

    @camera.setter
    def camera(self, camera: Camera):
        # TODO add old camera destructor
        # Set camera
        self._camera = camera
        # Update Renderables according to new camera
        self.renderables.update_camera(camera)

    def render(self, filepath: Union[str, Path] = "result.png", use_gpu=True, samples=128):
        if self.camera is None:
            raise RuntimeError("Can't render without a camera")

        filepath = Path(filepath)

        scene = bpy.data.scenes[0]
        scene.render.resolution_x = self.camera.resolution[0]
        scene.render.resolution_y = self.camera.resolution[1]
        scene.render.resolution_percentage = 100
        scene.render.filepath = str(filepath.parent)

        bpy.context.scene.camera = self.camera.blender_camera
        # bpy.context.object.data.dof.focus_object = object
        # input("Scene has been built. Press any key to start rendering")

        # Configure output
        bpy.context.scene.cycles.samples = samples
        bpy.context.scene.view_layers['View Layer'].use_pass_combined = True
        bpy.context.scene.view_layers['View Layer'].use_pass_diffuse_color = True
        bpy.context.scene.view_layers['View Layer'].use_pass_z = True
        scene_node_tree = bpy.context.scene.node_tree

        for n in scene_node_tree.nodes:
            scene_node_tree.nodes.remove(n)
        render_layer = scene_node_tree.nodes.new(type="CompositorNodeRLayers")
        output_image = scene_node_tree.nodes.new(type="CompositorNodeOutputFile")
        scene_node_tree.links.new(render_layer.outputs['Image'], output_image.inputs['Image'])

        # if save_depth:
        #     output_depth = scene_node_tree.nodes.new(type="CompositorNodeOutputFile")
        #     output_depth.format.file_format = "OPEN_EXR"
        #     scene_node_tree.links.new(render_layer.outputs['Depth'], output_depth.inputs['Image'])
        #
        # if save_albedo:
        #     output_albedo = scene_node_tree.nodes.new(type="CompositorNodeOutputFile")
        #     scene_node_tree.links.new(render_layer.outputs['DiffCol'], output_albedo.inputs['Image'])

        if use_gpu:
            bpy.context.scene.cycles.device = 'GPU'

            for scene in bpy.data.scenes:
                scene.cycles.device = 'GPU'

            # Enable CUDA
            bpy.context.preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'

            # Enable and list all devices, or optionally disable CPU
            for devices in bpy.context.preferences.addons['cycles'].preferences.get_devices():
                for d in devices:
                    d.use = True
                    if d.type == 'CPU':
                        d.use = False

        # Render
        bpy.context.scene.frame_current = 0
        output_image.file_slots[0].path = str(filepath)
        # if save_albedo:
        #     output_albedo.file_slots[0].path = f"{frame_name:04d}.albedo."
        # if save_depth:
        #     output_depth.file_slots[0].path = f"{frame_name:04d}.depth."
        # for object in scene_object_list:
        #     object.update_to_closest(frame_ind)

        bpy.ops.render.render(write_still=False)

    @staticmethod
    def export(path: Union[str, Path]):
        bpy.ops.wm.save_as_mainfile(filepath=str(path))

    @staticmethod
    def attach_blend(path: Union[str, Path]):
        bpy.ops.wm.open_mainfile(filepath=str(path))
