import os
import shutil
import sys
import tempfile
import warnings
from contextlib import nullcontext
from pathlib import Path
from typing import Union, Sequence

import bpy
import numpy as np

os.environ["OPENCV_IO_ENABLE_OPENEXR"] = "1"
import cv2

from .cameras import PerspectiveCamera, OrthographicCamera
from .cameras.base import Camera
from .internal import Singleton
from .internal.io import catch_stdout
from .internal.types import Vector2d, Vector2di, Vector3d, Vector4d, RotationParams
from .internal import parser
from .lights import LightsCollection
from .renderables import RenderablesCollection


class Scene(metaclass=Singleton):
    def __init__(self):
        # Initialise Blender scene
        self.renderables = RenderablesCollection()
        self.lights = LightsCollection()
        self._camera = None
        self._reset_scene()

    @staticmethod
    def _set_default_blender_parameters():
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
        bpy.context.scene.view_settings.view_transform = 'Standard'
        bpy.context.scene.cycles.samples = 128  # Default value, can be changed in .render
        bpy.context.scene.frame_current = 0

    @staticmethod
    def _remove_all_objects():
        """Removes all objects from the scene. Previously used to remove the default cube"""
        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False)
        bpy.ops.outliner.orphans_purge()
        bpy.ops.outliner.orphans_purge()
        bpy.ops.outliner.orphans_purge()

    @staticmethod
    def _load_empty_scene():
        """Resets the scene to the empty state"""
        bpy.ops.wm.read_homefile(use_empty=True)
        bpy.ops.outliner.orphans_purge()

    def _reset_scene(self):
        """Resets the scene to the empty state"""
        with catch_stdout():
            self._load_empty_scene()
        scene = bpy.data.scenes[0]
        scene.world = bpy.data.worlds.new("BlendifyWorld")
        self._frame_number = 0
        self._set_default_blender_parameters()
        self.renderables._reset()
        self.lights._reset()
        self._camera = None

    def clear(self):
        """Clears the scene"""
        self._reset_scene()

    @property
    def camera(self) -> Camera:
        return self._camera

    def set_perspective_camera(
            self, resolution: Vector2di, focal_dist: float = None, fov_x: float = None, fov_y: float = None,
            center: Vector2d = None, near: float = 0.1, far: float = 100., tag: str = 'camera', rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None, translation: Vector3d = (0, 0, 0),
            resolution_percentage: int = 100
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
            rotation_mode (str): type of rotation representation.
                Can be one of the following:
                - "quaternionWXYZ" - WXYZ quaternion
                - "quaternionXYZW" - XYZW quaternion
                - "rotvec" - axis-angle representation of rotation
                - "rotmat" - 3x3 rotation matrix
                - "euler<mode>" - Euler angles with the specified order of rotation, e.g. XYZ, xyz, ZXZ, etc. Refer to scipy.spatial.transform.Rotation.from_euler for details.
                - "look_at" - look at rotation, the rotation is defined by the point to look at and, optional, the rotation around the forward direction vector (a single float value in tuple or list)
            rotation (RotationParams): rotation parameters according to the rotation_mode
                - for "quaternionWXYZ" and "quaternionXYZW" - Vec4d
                - for "rotvec" - Vec3d
                - for "rotmat" - Mat3x3
                - for "euler<mode>" - Vec3d
                - for "look_at" - Vec3d, Positionable or Tuple[Vec3d/Positionable, float], where float is the rotation around the forward direction vector in degrees
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            resolution_percentage (int, optional):
        Returns:
            PerspectiveCamera: created camera
        """
        camera = PerspectiveCamera(resolution=resolution, focal_dist=focal_dist, fov_x=fov_x, fov_y=fov_y,
                                   center=center, near=near, far=far, tag=tag,
                                   rotation_mode=rotation_mode, rotation=rotation, translation=translation)
        self._setup_camera(camera, resolution_percentage)
        return camera

    def set_orthographic_camera(
            self, resolution: Vector2di, ortho_scale: float = 1., near: float = 0.1, far: float = 100.,
            tag: str = 'camera', rotation_mode: str = "quaternionWXYZ",
            rotation: RotationParams = None, translation: Vector3d = (0, 0, 0),
            resolution_percentage: int = 100
    ) -> OrthographicCamera:
        """Set orthographic camera in the scene. Replaces the previous scene camera, if it exists

        Args:
            resolution (Vector2di): (w, h), the resolution of the resulting image
            ortho_scale (float, optional): Orthographic Camera scale (similar to zoom) (default: 1.0)
            near (float, optional): Camera near clipping distance (default: 0.1)
            far (float, optional): Camera far clipping distance (default: 100)
            tag (str): name of the created object in Blender
            rotation_mode (str): type of rotation representation.
                Can be one of the following:
                - "quaternionWXYZ" - WXYZ quaternion
                - "quaternionXYZW" - XYZW quaternion
                - "rotvec" - axis-angle representation of rotation
                - "rotmat" - 3x3 rotation matrix
                - "euler<mode>" - Euler angles with the specified order of rotation, e.g. XYZ, xyz, ZXZ, etc. Refer to scipy.spatial.transform.Rotation.from_euler for details.
                - "look_at" - look at rotation, the rotation is defined by the point to look at and, optional, the rotation around the forward direction vector (a single float value in tuple or list)
            rotation (RotationParams): rotation parameters according to the rotation_mode
                - for "quaternionWXYZ" and "quaternionXYZW" - Vec4d
                - for "rotvec" - Vec3d
                - for "rotmat" - Mat3x3
                - for "euler<mode>" - Vec3d
                - for "look_at" - Vec3d, Positionable or Tuple[Vec3d/Positionable, float], where float is the rotation around the forward direction vector in degrees
            translation (Vector3d, optional): translation applied to the Blender object (default: (0,0,0))
            resolution_percentage (int, optional):
        Returns:
            OrthographicCamera: created camera
        """
        camera = OrthographicCamera(resolution=resolution, ortho_scale=ortho_scale, far=far, near=near, tag=tag,
                                    rotation_mode=rotation_mode, rotation=rotation, translation=translation)
        self._setup_camera(camera, resolution_percentage)
        return camera

    def _setup_camera(self, camera: Camera, resolution_percentage: int = 100):
        # Delete old camera
        if self._camera is not None:
            self._camera._blender_remove_object()
        # Set new camera
        self._camera = camera
        scene = bpy.data.scenes[0]
        scene.render.resolution_x = camera.resolution[0]
        scene.render.resolution_y = camera.resolution[1]
        scene.render.resolution_percentage = resolution_percentage

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
        data = cv2.imread(path, cv2.IMREAD_UNCHANGED)[:, :, 0]
        data[data > dist_thresh] = -np.inf
        return data

    @staticmethod
    def read_image(path: str) -> np.ndarray:
        """Reads the image stored in PNG or JPG format

        Args:
            path (str): path to the image file

        Returns:
            np.ndarray: image in numpy array format
        """
        return cv2.cvtColor(cv2.imread(path, cv2.IMREAD_UNCHANGED), cv2.COLOR_BGRA2RGBA)

    def render(
            self, filepath: Union[str, Path] = None, use_gpu: bool = True, samples: int = 128,
            save_depth: bool = False, save_albedo: bool = False, verbose: bool = False,
            use_denoiser: bool = False, aa_filter_width: float = 1.5
    ):
        """Start the Blender rendering process

        Automatically detects if shadow catcher objects are present in the scene by checking is_shadow_catcher property
        of Blender objects. For rendering with shadow catchers background is made white, because since Blender 3.0
        shadow catcher rendering pass is made to be multiplied with the background.

        Args:
            filepath (Union[str, Path]): path to the image (PNG) to render to, returns the image as numpy array if None
            use_gpu (bool): whether to render on GPU or not
            samples (bool): number of raytracing samples per pixel
            save_depth (bool): whether to save the depth in the separate file.
              If yes, the numpy array <filepath>.depth.npy will be created if filepath is set, otherwise appends the array to the output.
            save_albedo (bool): whether to save albedo (raw color information) in the separate file.
              If yes, the PNG image <filepath>.albedo.png with color information will be created
              if filepath is set, otherwise appends the array to the output.
            verbose (bool): whether to allow blender to log its status to stdout during rendering
            use_denoiser (bool): use openimage denoiser to denoise the result
            aa_filter_width (float): width of the anti-aliasing filter, set 0 to turn off
        """
        if self.camera is None:
            raise RuntimeError("Can't render without a camera")

        # setup anti-aliasing
        aa_filter_width = max(0, aa_filter_width)
        bpy.context.scene.cycles.filter_width = aa_filter_width
        bpy.context.scene.cycles.pixel_filter_type = 'BLACKMAN_HARRIS'
        if save_depth and aa_filter_width != 0:
            warnings.warn("Anti-aliasing filter is enabled. Saved depth will not be exact.")

        render_to_ram = filepath is None
        with tempfile.TemporaryDirectory() if render_to_ram else nullcontext() as tmpdir:
            if render_to_ram:
                basepath = tmpdir
                filename = 'result.png'
                filepath = Path(tmpdir) / filename
            else:
                filepath = Path(filepath)
                basepath = str(filepath.parent.absolute())
                filename = filepath.stem

            scene = bpy.data.scenes[0]
            scene.render.resolution_x = self.camera.resolution[0]
            scene.render.resolution_y = self.camera.resolution[1]
            scene.render.resolution_percentage = 100
            scene.render.filepath = str(basepath)

            bpy.context.scene.camera = self.camera.blender_camera
            # bpy.context.object.data.dof.focus_object = object
            # input("Scene has been built. Press any key to start rendering")

            # Setup denoising
            if use_denoiser:
                bpy.context.scene.cycles.use_denoising = True
                bpy.context.scene.cycles.denoiser = 'OPENIMAGEDENOISE'
                bpy.context.scene.view_layers[0].cycles.use_denoising = True
                bpy.context.view_layer.cycles.denoising_store_passes = True
            else:
                bpy.context.scene.cycles.use_denoising = False
                bpy.context.scene.view_layers[0].cycles.use_denoising = False
                bpy.context.view_layer.cycles.denoising_store_passes = False

            # Configure output
            bpy.context.scene.cycles.samples = samples
            bpy.context.scene.view_layers['ViewLayer'].use_pass_combined = True
            bpy.context.scene.view_layers['ViewLayer'].use_pass_diffuse_color = True
            bpy.context.scene.view_layers['ViewLayer'].use_pass_z = True
            scene_node_tree = bpy.context.scene.node_tree

            for n in scene_node_tree.nodes:
                scene_node_tree.nodes.remove(n)
            render_layer = scene_node_tree.nodes.new(type="CompositorNodeRLayers")

            # check if we have shadow catchers
            use_shadow_catcher = False
            for obj in bpy.data.objects:
                if obj.type != "LIGHT" and obj.is_shadow_catcher:
                    use_shadow_catcher = True
                    break

            # create output node
            if use_shadow_catcher:
                bpy.context.view_layer.cycles.use_pass_shadow_catcher = True
                alpha_over = scene_node_tree.nodes.new(type="CompositorNodeAlphaOver")
                scene_node_tree.links.new(render_layer.outputs['Shadow Catcher'], alpha_over.inputs[1])
                scene_node_tree.links.new(render_layer.outputs['Image'], alpha_over.inputs[2])

                output_image = scene_node_tree.nodes.new(type="CompositorNodeOutputFile")
                scene_node_tree.links.new(alpha_over.outputs['Image'], output_image.inputs['Image'])
            else:
                bpy.context.view_layer.cycles.use_pass_shadow_catcher = False
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

                # Detect the appropriate GPU rendering mode
                rendering_mode_priority_list = ['OPTIX', 'HIP', 'ONEAPI', 'CUDA']
                rendering_preferences = bpy.context.preferences.addons['cycles'].preferences
                rendering_preferences.refresh_devices()
                devices = rendering_preferences.devices
                available_rendering_modes = set()
                for dev in devices:
                    available_rendering_modes.add(dev.type)
                chosen_rendering_mode = "NONE"
                for mode in rendering_mode_priority_list:
                    if mode in available_rendering_modes:
                        chosen_rendering_mode = mode
                        break

                # Set GPU rendering mode to detected one
                rendering_preferences.compute_device_type = chosen_rendering_mode

                # Optionally, list the devices before rendering
                # for dev in devices:
                #     print(f"ID:{dev.id} Name:{dev.name} Type:{dev.type} Use:{dev.use}")

            # Render
            bpy.context.scene.frame_current = self._frame_number
            temp_filesuffix = next(tempfile._get_candidate_names())
            temp_filepath = str(filepath) + "." + temp_filesuffix
            render_suffixes = [f".color.######.png"]
            if save_depth:
                render_suffixes.append(f".depth.######.exr")
            if save_albedo:
                render_suffixes.append(f".albedo.######.png")
            while self.check_any_exists(temp_filepath, render_suffixes):
                temp_filesuffix = next(tempfile._get_candidate_names())
                temp_filepath = str(filepath) + "." + temp_filesuffix
            temp_filename = os.path.basename(temp_filepath)
            output_image.base_path = basepath
            output_image.file_slots[0].path = temp_filename + ".color."
            if save_depth:
                output_depth.file_slots[0].path = temp_filename + ".depth."
            if save_albedo:
                output_albedo.file_slots[0].path = temp_filename + ".albedo."

            with catch_stdout(skip=verbose):
                bpy.ops.render.render(write_still=False)

            if render_to_ram:
                image_data = self.read_image(temp_filepath + f".color.{self._frame_number:04d}.png")
                outputs = [image_data]
                if save_depth:
                    distmap = self.read_exr_distmap(temp_filepath + f".depth.{self._frame_number:04d}.exr", dist_thresh=self.camera.far * 1.1)
                    depthmap = self.camera.distance2depth(distmap)
                    outputs.append(depthmap)
                if save_albedo:
                    albedomap = self.read_image(temp_filepath + f".albedo.{self._frame_number:04d}.png")
                    outputs.append(albedomap)
                if len(outputs) == 1:
                    return outputs[0]
                else:
                    return outputs
            else:
                shutil.move(temp_filepath + f".color.{self._frame_number:04d}.png", filepath)
                output_image.file_slots[0].path = filename
                if save_depth:
                    distmap = self.read_exr_distmap(temp_filepath + f".depth.{self._frame_number:04d}.exr", dist_thresh=self.camera.far * 1.1)
                    depthmap = self.camera.distance2depth(distmap)
                    np.save(os.path.splitext(filepath)[0] + ".depth.npy", depthmap)
                    os.remove(temp_filepath + f".depth.{self._frame_number:04d}.exr")
                    output_depth.file_slots[0].path = filename + ".depth."
                if save_albedo:
                    shutil.move(temp_filepath + f".albedo.{self._frame_number:04d}.png", os.path.splitext(filepath)[0] + ".albedo.png")
                    output_albedo.file_slots[0].path =  filename + ".albedo."

    def preview(self, filepath: Union[str, Path] = None, save_depth: bool = False, save_albedo: bool = False, verbose: bool = False, fast: bool = False):
        """Renders a scene using Blender's OpenGL renderer. Linux and MacOS Only.

                Args:
                    filepath (Union[str, Path]): path to the image (PNG) to render to, returns the image as numpy array if None
                    use_gpu (bool): whether to render on GPU or not
                    samples (bool): number of raytracing samples per pixel
                    save_depth (bool): whether to save the depth in the separate file.
                      If yes, the numpy array <filepath>.depth.npy will be created if filepath is set, otherwise appends the array to the output.
                    save_albedo (bool): whether to save albedo (raw color information) in the separate file.
                      If yes, the PNG image <filepath>.albedo.png with color information will be created
                      if filepath is set, otherwise appends the array to the output.
                    verbose (bool): whether to allow blender to log its status to stdout during rendering
                    use_denoiser (bool): use openimage denoiser to denoise the result
                    fast (bool): whether to use fast and colorless preview mode (workbench engine)
                """
        assert sys.platform.startswith('linux') or sys.platform.startswith('darwin'), "Preview is only supported on Linux and MacOS"

        # Switch to OpenGL renderer
        if not fast:
            bpy.context.scene.render.engine = 'BLENDER_EEVEE'
        else:
            bpy.context.scene.render.engine = 'BLENDER_WORKBENCH'

        if self.camera is None:
            raise RuntimeError("Can't render without a camera")

        render_to_ram = filepath is None
        with tempfile.TemporaryDirectory() if render_to_ram else nullcontext() as tmpdir:
            if render_to_ram:
                basepath = tmpdir
                filename = 'result.png'
                filepath = Path(tmpdir) / filename
            else:
                filepath = Path(filepath)
                basepath = str(filepath.parent.absolute())
                filename = filepath.stem

            scene = bpy.data.scenes[0]
            scene.render.resolution_x = self.camera.resolution[0]
            scene.render.resolution_y = self.camera.resolution[1]
            scene.render.resolution_percentage = 100
            scene.render.filepath = str(filepath.parent)

            bpy.context.scene.camera = self.camera.blender_camera
            # bpy.context.object.data.dof.focus_object = object
            # input("Scene has been built. Press any key to start rendering")

            bpy.context.scene.view_layers['ViewLayer'].use_pass_combined = True
            bpy.context.scene.view_layers['ViewLayer'].use_pass_diffuse_color = True
            bpy.context.scene.view_layers['ViewLayer'].use_pass_z = True
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

            # Render
            bpy.context.scene.frame_current = self._frame_number
            temp_filesuffix = next(tempfile._get_candidate_names())
            temp_filepath = str(filepath) + "." + temp_filesuffix
            render_suffixes = [f".color.{self._frame_number:04d}.png"]
            if save_depth:
                render_suffixes.append(f".depth.{self._frame_number:04d}.exr")
            if save_albedo:
                render_suffixes.append(f".albedo.{self._frame_number:04d}.png")
            while self.check_any_exists(temp_filepath, render_suffixes):
                temp_filesuffix = next(tempfile._get_candidate_names())
                temp_filepath = str(filepath) + "." + temp_filesuffix
            temp_filename = os.path.basename(temp_filepath)
            output_image.base_path = basepath
            output_image.file_slots[0].path = temp_filename + ".color."
            if save_depth:
                output_depth.file_slots[0].path = temp_filename + ".depth."
            if save_albedo:
                output_albedo.file_slots[0].path = temp_filename + ".albedo."

            with catch_stdout(skip=verbose):
                bpy.ops.render.render(write_still=False)

            if render_to_ram:
                image_data = self.read_image(temp_filepath + f".color.{self._frame_number:04d}.png")
                outputs = [image_data]
                if save_depth:
                    distmap = self.read_exr_distmap(temp_filepath + f".depth.{self._frame_number:04d}.exr", dist_thresh=self.camera.far * 1.1)
                    depthmap = self.camera.distance2depth(distmap)
                    outputs.append(depthmap)
                if save_albedo:
                    albedomap = self.read_image(temp_filepath + f".albedo.{self._frame_number:04d}.png")
                    outputs.append(albedomap)
                if len(outputs) == 1:
                    return outputs[0]
                else:
                    return outputs
            else:
                shutil.move(temp_filepath + f".color.{self._frame_number:04d}.png", filepath)
                output_image.file_slots[0].path = filename
                if save_depth:
                    distmap = self.read_exr_distmap(temp_filepath + f".depth.{self._frame_number:04d}.exr", dist_thresh=self.camera.far * 1.1)
                    depthmap = self.camera.distance2depth(distmap)
                    np.save(os.path.splitext(filepath)[0] + ".depth.npy", depthmap)
                    os.remove(temp_filepath + f".depth.{self._frame_number:04d}.exr")
                    output_depth.file_slots[0].path = filename + ".depth."
                if save_albedo:
                    shutil.move(temp_filepath + f".albedo.{self._frame_number:04d}.png", os.path.splitext(filepath)[0] + ".albedo.png")
                    output_albedo.file_slots[0].path = filename + ".albedo."

        # Return to Cycles renderer
        bpy.context.scene.render.engine = 'CYCLES'


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
    def export(path: Union[str, Path], include_file_textures: bool = True, verbose: bool = False):
        """Export the current scene to the .blend file

        Args:
            path (Union[str, Path]): path to the target .blend file
            include_file_textures (bool): whether to write textures loaded from external files inside .blend file
            verbose (bool): whether to allow blender to log its status to stdout during exporting
        """
        # hack to overcome Blender error message "BKE_bpath_relative_convert: basedir='', this is a bug"
        path = str(os.path.abspath(path))

        # Create folder
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        with catch_stdout(skip=verbose):
            if include_file_textures:
                bpy.ops.file.pack_all()
            bpy.ops.wm.save_as_mainfile(filepath=path)

    def attach_blend(self, path: Union[str, Path], with_camera: bool = False):
        """Append objects and materials from the existing .blend file to the scene.
        The only two modalities that can be added to blendify Scene are lights and optionally camera,
        others (renderable objects, materials, etc.) are only appended.
        The appended modalities will only be present in the internal Blender structures,
        but will not be added to the blendify Scene class structure.
        However, they will appear on rendering and in the exported .blend files

        Args:
            path: path to the .blend file to append the contents from
            with_camera: parse camera parameters from the .blend file or keep existing camera
        """
        main_scene_name = bpy.data.scenes.keys()[0]
        materials = []
        with (bpy.data.libraries.load(str(path), link=False) as (data_from, data_to)):
            for name in data_from.materials:
                materials.append({'name': name})

            if with_camera:
                # Check number of cameras by looking at cameras settings
                assert len(data_from.cameras) == 1, \
                    f"Expect to have only single camera in .blend, got {len(data_from.cameras)}"

                # Parse resolution parameters from scene
                assert len(data_from.scenes) == 1, \
                        f"Expect to have only single scene in .blend, got {len(data_from.scenes)}"

            data_to.scenes = data_from.scenes

        if with_camera:
            # Parse resolution
            res_x = data_to.scenes[0].render.resolution_x
            res_y = data_to.scenes[0].render.resolution_y
            resolution_percentage = data_to.scenes[0].render.resolution_percentage
            resolution = np.array([res_x, res_y])

            # Delete old camera
            if self._camera is not None:
                self._camera._blender_remove_object()
        else:
            # Remove camera from the imported scene
            camera_obj = data_to.scenes[0].camera

            with bpy.context.temp_override(selected_objects=[camera_obj]):
                bpy.ops.object.delete()

        # Add materials to the current scene
        if len(materials) > 0:
            bpy.ops.wm.append(directory=str(path) + "/Material/", files=materials, link=True)

        # Recursively copy collection
        main_scene = bpy.data.scenes[main_scene_name]
        import_scene = data_to.scenes[0]
        parser.move_collection(main_scene.collection, import_scene.collection)

        # Remove scene
        bpy.data.scenes.remove(import_scene, do_unlink=True)

        # Parse selected objects (lights and camera)
        bpy.context.view_layer.update()
        for obj in bpy.data.objects:
            if with_camera and obj.type == "CAMERA":
                camera_type, camera_dict = parser.parse_camera_from_blendfile(obj, resolution)

                # Remove current camera, because we need to recreate it
                bpy.data.cameras.remove(bpy.data.cameras[0])

                if camera_type == "ORTHO":
                    self.set_orthographic_camera(
                        resolution_percentage=resolution_percentage, **camera_dict
                    )
                elif camera_type == "PERSP":
                    self.set_perspective_camera(
                        resolution_percentage=resolution_percentage, **camera_dict
                    )
                else:
                    raise NotImplementedError(f"Unsupported camera type {camera_type}")
            elif obj.type == "LIGHT":
                light_type, light_dict = parser.parse_light_from_blendfile(obj)

                # Remove light before re-creaing it
                with bpy.context.temp_override(selected_objects=[obj]):
                    bpy.ops.object.delete()

                if light_type == "POINT":
                    self.lights.add_point(**light_dict)
                elif light_type == "SUN":
                    self.lights.add_sun(**light_dict)
                elif light_type == "SPOT":
                    self.lights.add_spot(**light_dict)
                elif light_type == "AREA":
                    self.lights.add_area(**light_dict)
                else:
                    raise NotImplementedError(f"Unsupported light type {light_type}")
