import torch
import trimesh
import logging
import json
import os
import numpy as np
import smplpytorch

from tqdm import tqdm
from skimage.io import imread
from videoio import VideoWriter
from scipy.spatial.transform.rotation import Rotation
from smplpytorch.pytorch.smpl_layer import SMPL_Layer
from blendify import get_scene
from blendify.renderables.materials import PrinsipledBSDFMaterial
from blendify.renderables.colors import UniformColors, FileTextureColors, FacesUV



class SMPLWrapper:
    """A wrapper for the smplpytorch layer"""

    def __init__(self, smpl_root: str, gender: str, shape_params: np.ndarray, device: torch.device = None):
        self.device = torch.device(device if device is not None else "cpu")
        self.smpl_root = smpl_root
        self.shape_params = self._preprocess_param(shape_params)
        self.smpl_layer = SMPL_Layer(center_idx=0, gender=gender, model_root=self.smpl_root).to(self.device)
        self.faces = self.smpl_layer.th_faces.cpu().numpy()

    def _preprocess_param(self, param: np.ndarray) -> torch.Tensor:
        """Prepare the parameters for SMPL layer"""
        if not isinstance(param, torch.Tensor):
            param = torch.tensor(param, dtype=torch.float32)
        param = param.to(self.device)
        return param

    def get_smpl(self, pose_params: np.ndarray, translation_params: np.ndarray) -> np.ndarray:
        """
        Get the SMPL mesh vertices from the target pose and global translation
        Args:
            pose_params: Pose parameters vector of shape (72)
            translation_params: Global translation vector of shape (3)
        Returns:
            np.ndarray: vertices of SMPL model
        """
        pose_params = self._preprocess_param(pose_params)
        translation_params = self._preprocess_param(translation_params)
        verts, joints = self.smpl_layer(th_pose_axisang=pose_params.unsqueeze(0),
                                        th_betas=self.shape_params.unsqueeze(0))
        return (verts.squeeze(0) + translation_params.unsqueeze(0)).cpu().numpy()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("animated_smpl_example")

# Set the target rendering parameters
resolution = (1280, 720)
fps = 30
tmp_frame_path = "05_assets/temp_frame.png"  # This is the name of the temporary file to store each frame
output_video_path = "05_assets/output_rendering.mp4"

# Load the scene (don't forget to download resources with 05_download_assets.sh
logger.info("Loading scene resources...")
trimesh_mesh = trimesh.load("05_assets/scene_mesh.ply")
uv_map = np.load("05_assets/scene_face_uvmap.npy")
texture_path = "05_assets/scene_texture.jpg"
verts = np.array(trimesh_mesh.vertices)
faces = np.array(trimesh_mesh.faces)

# Load SMPL params and initialize the model
logger.info("Loading SMPL animation..")
animation_params = json.load(open("05_assets/animation_data.json"))
# Set different smpl_root to SMPL .pkl files folder if needed
# Make sure to fix the typo for male model while unpacking SMPL .pkl files:
# basicmodel_m_lbs_10_207_0_v1.0.0.pkl -> basicModel_m_lbs_10_207_0_v1.0.0.pkl
smpl_model = SMPLWrapper(smpl_root=os.path.join(os.path.dirname(smplpytorch.__file__), "native/models"),
                         gender=animation_params["static_params"]["smpl_gender"],
                         shape_params=animation_params["static_params"]["smpl_shape"])

logger.info("Setting up the Blender scene")
scene = get_scene()

# Add the camera
camera = scene.add_perspective_camera(resolution, fov_y=np.deg2rad(75))

# Define the materials
smpl_material = PrinsipledBSDFMaterial()
pc_material = PrinsipledBSDFMaterial()
pc_material.specular = 1.0
pc_material.roughness = 1.0
bl_scene_colors = FileTextureColors(texture_path, FacesUV(uv_map))

# Add the scene mesh; turn off shadowing as the shadows are already baked in the texture
bl_scene = scene.renderables.add_mesh(vertices=verts, faces=faces, material=pc_material, colors=bl_scene_colors)
bl_scene.emit_shadows = False

# Add the SMPL mesh, set the pose to zero for the first frame, just to initialize
smpl_vertices = smpl_model.get_smpl(np.zeros(72), np.zeros(3))
smpl_faces = smpl_model.faces
bl_smpl_colors = UniformColors((0.3, 0.3, 0.3))
bl_smpl_mesh = scene.renderables.add_mesh(smpl_vertices, smpl_faces, smpl_material, bl_smpl_colors)
bl_smpl_mesh.set_smooth()  # Force the surface of model to look smooth

# Set the lights; one main sunlight and a secondary light without visible shadows to make the scene overall brighter
sunlight = scene.lights.add_sun(strength=4.3,
                                quaternion=np.roll(Rotation.from_euler('yz', (-45, -90), degrees=True).as_quat(), 1))
sunlight2 = scene.lights.add_sun(strength=5,
                                 quaternion=np.roll(Rotation.from_euler('yz', (-45, 165), degrees=True).as_quat(), 1))
sunlight2.cast_shadows = False

# Rendering loop
logger.info("Entering the main drawing loop")
with VideoWriter(output_video_path, resolution=resolution, fps=fps) as vw:
    for curr_params in tqdm(animation_params["dynamic_params"]):
        smpl_pose = np.array(curr_params["smpl_pose"])
        smpl_translation = np.array(curr_params["smpl_translation"])
        camera_quaternion = np.array(curr_params["camera_quaternion"])
        camera_translation = np.array(curr_params["camera_translation"])
        # Update the SMPL mesh for the current pose
        smpl_vertices = smpl_model.get_smpl(smpl_pose, smpl_translation)
        bl_smpl_mesh.update_vertices(smpl_vertices)
        # Set the current camera position
        camera.set_position(camera_quaternion, camera_translation)
        # Render the scene to image
        scene.render(tmp_frame_path, samples=128)
        # Read the resulting frame back
        img = imread(tmp_frame_path)
        # Frames have transparent background; perform an alpha blending with white background instead
        alpha = img[:, :, 3:4].astype(np.int32)
        img_white_bkg = ((img[:, :, :3] * alpha + 255 * (255 - alpha)) // 255).astype(np.uint8)
        # Add the frame to the video
        vw.write(img_white_bkg)
# Clean up
os.remove(tmp_frame_path)
logger.info("Rendering complete")
