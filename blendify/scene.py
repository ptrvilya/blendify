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
        self.camera: Camera = None

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
        bpy.context.scene.view_settings.view_transform = 'Raw'  # Important if you want to get a pure color background (eg. white background)
        bpy.context.scene.cycles.samples = 128  # Default value, can be changed in .render
        # Empty the scene
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)

    def update_camera(self, camera: Camera):
        # Set camera
        self.camera = camera
        # Update Renderables according to new camera
        self.renderables.update_camera(camera)
        # Update blender camera
        # scene = bpy.data.scenes[0]
        # scene.render.resolution_x = camera.resolution_x
        # scene.render.resolution_y = camera.resolution_y
        # scene.render.resolution_percentage = 100
        # TODO adapt this according to camera interfaces
        # camera_loc = annotation['camera']['location'] if 'location' in annotation['camera'] else (0, 0, 0)
        # camera_rot = annotation['camera']['rotation'] if 'rotation' in annotation['camera'] else (0, 0, 0)
        # bpy.ops.object.camera_add(location=camera_loc, rotation=camera_rot)
        # camera = bpy.data.objects['Camera']
        # camera.data.sensor_fit = "HORIZONTAL"
        # camera.data.angle = annotation['camera']['xfov']
        # camera.data.shift_x = annotation['camera']['shift_x']
        # camera.data.shift_y = annotation['camera']['shift_y']
        # # camera.data.lens_unit = "FOV"
        # bpy.context.scene.camera = camera

    def render(self):
        if self.camera is None:
            raise RuntimeError("Can't render without a camera")

    @staticmethod
    def export(path: Union[str, Path]):
        bpy.ops.wm.save_as_mainfile(filepath=str(path))

    @staticmethod
    def attach_blend(path: Union[str, Path]):
        bpy.ops.wm.open_mainfile(filepath=str(path))
