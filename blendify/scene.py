import array
import os
import shutil
import tempfile
from pathlib import Path
from typing import Union, Sequence

import bpy
import numpy as np

from .cameras import PerspectiveCamera, OrthographicCamera
from .cameras.base import Camera
from .internal import Singleton
from .internal.types import Vector2d, Vector2di, Vector3d, Vector4d
from .lights import LightsCollection
from .renderables import RenderablesCollection


class Scene(metaclass=Singleton):
    def __init__(self):
        # Initialise Blender scene
        self._set_default_blender_scene()

        self.renderables = RenderablesCollection()
        self.lights = LightsCollection()
        self._camera = None

    @staticmethod
    def _set_default_blender_scene():
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
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        bpy.ops.outliner.orphans_purge()
        bpy.ops.outliner.orphans_purge()
        bpy.ops.outliner.orphans_purge()

    @property
    def camera(self) -> Camera:
        return self._camera

    def set_perspective_camera(
        self, resolution: Vector2di, focal_dist: float = None, fov_x: float = None, fov_y: float = None,
        center: Vector2d = None, near: float = 0.1, far: float = 100., tag: str = 'camera',
        quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0)
    ) -> PerspectiveCamera:
        """Set perspective camera in the scene. Replaces the previous scene camera, if it exists.
        One of focal_dist, fov_x or fov_y is required to set the camera parameters

        Args:
            resolution (Vector2di): (w, h), the resolution of the resulting image
            focal_dist (float, optional): Perspective Camera focal distance in millimeters (default: None)
            fov_x (float, optional): Camera lens horizontal field of view (default: None)
            fov_y (float, optional): Camera lens vertical field of view (default: None)
            center (Vector2d, optional): (x, y), horizontal and vertical shifts of the Camera (default: None)
            near (float, optional): Camera near clipping distance (default: 0.1)
            far (float, optional): Camera far clipping distance (default: 100)
            tag (str): name of the created object in Blender
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))

        Returns:
            PerspectiveCamera: created camera
        """
        camera = PerspectiveCamera(resolution=resolution, focal_dist=focal_dist, fov_x=fov_x, fov_y=fov_y,
                                   center=center, near=near, far=far, tag=tag,
                                   quaternion=quaternion, translation=translation)
        self._setup_camera(camera)
        return camera

    def set_orthographic_camera(
        self, resolution: Vector2di, ortho_scale: float = 1., near: float = 0.1, far: float = 100.,
        tag: str = 'camera', quaternion: Vector4d = (1, 0, 0, 0), translation: Vector3d = (0, 0, 0)
    ) -> OrthographicCamera:
        """Set orthographic camera in the scene. Replaces the previous scene camera, if it exists

        Args:
            resolution (Vector2di): (w, h), the resolution of the resulting image
            ortho_scale (float, optional): Orthographic Camera scale (similar to zoom) (default: 1.0)
            near (float, optional): Camera near clipping distance (default: 0.1)
            far (float, optional): Camera far clipping distance (default: 100)
            tag (str): name of the created object in Blender
            quaternion (Vector4d, optional): rotation applied to the Blender object (default: (1,0,0,0))
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))

        Returns:
            OrthographicCamera: created camera
        """
        camera = OrthographicCamera(resolution=resolution, ortho_scale=ortho_scale, far=far, near=near, tag=tag,
                                    quaternion=quaternion, translation=translation)
        self._setup_camera(camera)
        return camera

    def _setup_camera(self, camera: Camera):
        # Delete old camera
        if self._camera is not None:
            self._camera._blender_remove_object()
        # Set new camera
        self._camera = camera
        scene = bpy.data.scenes[0]
        scene.render.resolution_x = camera.resolution[0]
        scene.render.resolution_y = camera.resolution[1]
        scene.render.resolution_percentage = 100

    @staticmethod
    def read_exr_distmap(path: str, dist_thresh: float = 1e4) -> np.ndarray:
        """Reads the distance map stored in EXR format, filters out all the values after a certain distance threshold.
        Requires OpenEXR to be installed in the system

        Args:
            path (str): path to the .exr file
            dist_thresh (float): distance clip threshold

        Returns:
            np.ndarray: distance map in numpy array format
        """
        import OpenEXR
        import Imath
        exr_input = OpenEXR.InputFile(path)
        exr_float_type = Imath.PixelType(Imath.PixelType.FLOAT)
        data = np.array(array.array('f', exr_input.channel("R", exr_float_type)).tolist())
        data[data > dist_thresh] = -np.inf
        return data

    def render(
        self, filepath: Union[str, Path] = "result.png", use_gpu: bool = True, samples: int = 128,
        save_depth: bool = False, save_albedo: bool = False
    ):
        """Start the Blender rendering process

        Args:
            filepath (Union[str, Path]): path to the image (PNG) to render to
            use_gpu (bool): whether to render on GPU or not
            samples (bool): number of raytracing samples per pixel
            save_depth (bool): whether to save the depth in the separate file.
              If yes, the numpy array <filepath>.depth.npy will be created.
            save_albedo (bool): whether to save albedo (raw color information) in the separate file.
              If yes, the PNG image <filepath>.albedo.png with color information will be created.
        """
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
        temp_filesuffix = next(tempfile._get_candidate_names())
        temp_filepath = str(filepath) + "." + temp_filesuffix
        render_suffixes = [".color.0000.png"]
        if save_depth:
            render_suffixes.append(".depth.0000.exr")
        if save_albedo:
            render_suffixes.append(".albedo.0000.png")
        while self.check_any_exists(temp_filepath, render_suffixes):
            temp_filesuffix = next(tempfile._get_candidate_names())
            temp_filepath = str(filepath) + "." + temp_filesuffix
        temp_filename = os.path.basename(temp_filepath)
        output_image.file_slots[0].path = temp_filename + ".color."
        if save_depth:
            output_depth.file_slots[0].path = temp_filename + ".depth."
        if save_albedo:
            output_albedo.file_slots[0].path = temp_filename + ".albedo."

        bpy.ops.render.render(write_still=False)

        shutil.move(temp_filepath + ".color.0000.png", filepath)
        if save_depth:
            distmap = self.read_exr_distmap(temp_filepath + ".depth.0000.exr", dist_thresh=self.camera.far*1.1)
            distmap = distmap.reshape(self.camera.resolution[::-1])
            depthmap = self.camera.distance2depth(distmap)
            np.save(os.path.splitext(filepath)[0] + ".depth.npy", depthmap)
            os.remove(temp_filepath + ".depth.0000.exr")
        if save_albedo:
            shutil.move(temp_filepath + ".albedo.0000.png", os.path.splitext(filepath)[0] + ".albedo.png")

    @staticmethod
    def check_any_exists(fileprefix: str, filesuffixes: Sequence[str]) -> bool:
        """Check if any of the combinations of <fileprefix>+<any filesuffix> exist in the filesystem

        Args:
            fileprefix (str): single file prefix, can the full path or local name
            filesuffixes (Sequence[str]): a sequence of file suffixes to choose from

        Returns:
            bool: True is any of the combinations exists in the filesystem, False otherwise
        """
        for filesuffix in filesuffixes:
            fullpath = fileprefix + filesuffix
            if os.path.exists(fullpath):
                return True
        return False

    @staticmethod
    def export(path: Union[str, Path], include_file_textures: bool = True):
        """Export the current scene to the .blend file

        Args:
            path (Union[str, Path]): path to the target .blend file
            include_file_textures (bool): whether to write textures loaded from external files inside .blend file
        """
        # hack to overcome BKE_bpath_relative_convert: basedir='', this is a bug
        path = str(os.path.abspath(path))

        if include_file_textures:
            bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=path)

    @staticmethod
    def attach_blend(path: Union[str, Path]):
        """Append all the contents of the existing .blend file to the scene.
        This includes lights, cameras, renderable objects, parameters, materials, etc.
        The appended modalities will only be present in the internal Blender structures,
        but not be present in the Scene class structure.
        However, they will appear on rendering and in the exported .blend files

        Args:
            path: path to the .blend file to append the contents from
        """
        objects, materials = [], []
        with bpy.data.libraries.load(str(path), link=False) as (data_from, data_to):
            # data_to.materials = data_from.materials
            for name in data_from.materials:
                materials.append({'name': name})

            for name in data_from.objects:
                objects.append({'name': name})

        bpy.ops.wm.append(directory=str(path) + "/Object/", files=objects)
        bpy.ops.wm.append(directory=str(path) + "/Material/", files=materials)
