import os
import tempfile
import shutil
import numpy as np
import array

from typing import Union, Sequence
from pathlib import Path

import bpy

from .lights import LightsCollection
from .renderables import RenderablesCollection
from .internal import Singleton
from .internal.types import Vector2d, Vector2di, Vector3d, Vector4d
from .cameras import Camera, PerspectiveCamera, OrthographicCamera


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

    def add_perspective_camera(self, resolution: Vector2di, focal_dist: float = None, fov_x: float = None,
                               fov_y: float = None, center: Vector2d = None, tag: str = 'camera',
                               quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0)):
        camera = PerspectiveCamera(resolution, focal_dist, fov_x, fov_y, center, tag, quaternion, translation)
        self._setup_camera(camera)

    def add_orthographic_camera(self, resolution: Vector2di, ortho_scale: float = 1.,
                                far: float = 1., near: float = 0.1, tag: str = 'camera',
                                quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0)):
        camera = OrthographicCamera(resolution, ortho_scale, far, near, tag, quaternion, translation)
        self._setup_camera(camera)

    def _setup_camera(self, camera: Camera):
        # TODO add old camera destructor
        # Set camera
        self._camera = camera
        scene = bpy.data.scenes[0]
        scene.render.resolution_x = camera.resolution[0]
        scene.render.resolution_y = camera.resolution[1]
        scene.render.resolution_percentage = 100
        # Update Renderables according to new camera
        self.renderables.update_camera(camera)

    @staticmethod
    def read_exr_distmap(path, dist_thresh=1e4):
        import OpenEXR
        import Imath
        exr_input = OpenEXR.InputFile(path)
        exr_float_type = Imath.PixelType(Imath.PixelType.FLOAT)
        data = np.array(array.array('f', exr_input.channel("R", exr_float_type)).tolist())
        data[data > dist_thresh] = -np.inf
        return data

    def render(self, filepath: Union[str, Path] = "result.png", use_gpu=True, samples=128, save_depth = False, save_albedo = False):
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

        if save_depth:
            output_depth = scene_node_tree.nodes.new(type="CompositorNodeOutputFile")
            output_depth.format.file_format = "OPEN_EXR"
            scene_node_tree.links.new(render_layer.outputs['Depth'], output_depth.inputs['Image'])

        if save_albedo:
            output_albedo = scene_node_tree.nodes.new(type="CompositorNodeOutputFile")
            scene_node_tree.links.new(render_layer.outputs['DiffCol'], output_albedo.inputs['Image'])

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
        temp_filesuff = next(tempfile._get_candidate_names())
        temp_filepath = str(filepath)+"."+temp_filesuff
        # dirpath = os.path.dirname(filepath)
        render_suffixes = [".color.0000.png"]
        if save_depth:
            render_suffixes.append(".depth.0000.exr")
        if save_albedo:
            render_suffixes.append(".albedo.0000.png")
        while self.check_any_exists(temp_filepath, render_suffixes):
            temp_filesuff = next(tempfile._get_candidate_names())
            temp_filepath = str(filepath)+"."+temp_filesuff
        output_image.file_slots[0].path = temp_filepath+".color."
        if save_depth:
            output_depth.file_slots[0].path = temp_filepath+".depth."
        if save_albedo:
            output_albedo.file_slots[0].path = temp_filepath+".albedo."

        bpy.ops.render.render(write_still=False)

        shutil.move(temp_filepath+".color.0000.png", filepath)
        if save_depth:
            distmap = self.read_exr_distmap(temp_filepath+".depth.0000.exr")
            distmap = distmap.reshape(self.camera.resolution[::-1])
            depthmap = self.camera.distance2depth(distmap)
            np.save(os.path.splitext(filepath)[0]+".depth.npy", depthmap)
            os.remove(temp_filepath+".depth.0000.exr")
        if save_albedo:
            shutil.move(temp_filepath + ".albedo.0000.png", os.path.splitext(filepath)[0]+".albedo.png")



    @staticmethod
    def check_any_exists(fileprefix:str, filesuffixes:Sequence[str]):
        for filesuffix in filesuffixes:
            fullpath = fileprefix+filesuffix
            if os.path.exists(fullpath):
                return True
        return False

    @staticmethod
    def export(path: Union[str, Path]):
        bpy.ops.wm.save_as_mainfile(filepath=str(path))

    @staticmethod
    def attach_blend(path: Union[str, Path]):
        # bpy.ops.wm.open_mainfile(filepath=str(path))
        # bpy.ops.wm.append(filepath=str(path))
        objects, materials = [], []
        with bpy.data.libraries.load(str(path), link=False) as (data_from, data_to):
            # data_to.materials = data_from.materials
            for name in data_from.materials:
                materials.append({'name': name})

            for name in data_from.objects:
                objects.append({'name': name})

        bpy.ops.wm.append(directory=str(path) + "/Object/", files=objects)
        bpy.ops.wm.append(directory=str(path) + "/Material/", files=materials)

        # # append everything
        # with bpy.data.libraries.load(filepath) as (data_from, data_to):
        #     for attr in dir(data_to):
        #         setattr(data_to, attr, getattr(data_from, attr))
        #
        # # load a single scene we know the name of.
        # with bpy.data.libraries.load(filepath) as (data_from, data_to):
        #     data_to.scenes = ["Scene"]
