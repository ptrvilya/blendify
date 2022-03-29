import argparse
import json
import logging
import os

import numpy as np
import smplpytorch
import trimesh
from scipy.spatial.transform.rotation import Rotation
from skimage.io import imread
from videoio import VideoWriter
from urllib import request

from blendify import get_scene
from blendify.renderables.colors import UniformColors, FileTextureColors, FacesUV
from blendify.renderables.materials import PrinsipledBSDFMaterial
from blendify.utils.smpl_wrapper import SMPLWrapper
from blendify.utils.image import blend_with_background


def main(args):
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("Blendify 05 example")
    # Load the scene (don't forget to download resources with 05_download_assets.sh
    logger.info("Loading scene resources...")
    trimesh_mesh = trimesh.load("./assets/05_smpl_movement/scene_mesh.ply")
    uv_map = np.load("./assets/05_smpl_movement/scene_face_uvmap.npy")
    texture_path = "./assets/05_smpl_movement/scene_texture.jpg"
    verts = np.array(trimesh_mesh.vertices)
    faces = np.array(trimesh_mesh.faces)

    # Load SMPL params and initialize the model
    logger.info("Loading SMPL animation..")
    animation_params = json.load(open("./assets/05_smpl_movement/animation_data.json"))
    # Set different smpl_root to SMPL .pkl files folder if needed
    # Make sure to fix the typo for male model while unpacking SMPL .pkl files:
    # basicmodel_m_lbs_10_207_0_v1.0.0.pkl -> basicModel_m_lbs_10_207_0_v1.0.0.pkl
    smpl_model = SMPLWrapper(smpl_root=os.path.join(os.path.dirname(smplpytorch.__file__), "native/models"),
                             gender=animation_params["static_params"]["smpl_gender"],
                             shape_params=animation_params["static_params"]["smpl_shape"])

    logger.info("Setting up the Blender scene")
    scene = get_scene()

    # Add the camera
    camera = scene.set_perspective_camera(args.resolution, fov_y=np.deg2rad(75))

    # Define the materials
    # Material and Colors for SMPL mesh
    smpl_material = PrinsipledBSDFMaterial()
    smpl_colors = UniformColors((0.3, 0.3, 0.3))
    # Material and Colors for background scene mesh
    scene_mesh_material = PrinsipledBSDFMaterial()
    scene_mesh_material.specular = 1.0
    scene_mesh_material.roughness = 1.0
    scene_mesh_colors = FileTextureColors(texture_path, FacesUV(uv_map))

    # Add the background scene mesh; turn off shadowing as the shadows are already baked in the texture
    scene_mesh = scene.renderables.add_mesh(
        vertices=verts, faces=faces, material=scene_mesh_material, colors=scene_mesh_colors
    )
    scene_mesh.emit_shadows = False

    # Add the SMPL mesh, set the pose to zero for the first frame, just to initialize
    smpl_vertices = smpl_model.get_smpl(np.zeros(72), np.zeros(3))
    smpl_faces = smpl_model.faces
    smpl_mesh = scene.renderables.add_mesh(smpl_vertices, smpl_faces, smpl_material, smpl_colors)
    smpl_mesh.set_smooth()  # Force the surface of model to look smooth

    # Set the lights; one main sunlight and a secondary light without visible shadows to make the scene overall brighter
    sunlight = scene.lights.add_sun(
        strength=4.3, quaternion=np.roll(Rotation.from_euler('yz', (-45, -90), degrees=True).as_quat(), 1)
    )
    sunlight2 = scene.lights.add_sun(
        strength=5, quaternion=np.roll(Rotation.from_euler('yz', (-45, 165), degrees=True).as_quat(), 1)
    )
    sunlight2.cast_shadows = False

    # Optionally save blend file with the scene at frame 0
    if args.output_blend is not None:
        scene.export(args.output_blend)

    # Rendering loop
    tmp_frame_path = "./assets/05_tmp_frame.png"  # This is the name of the temporary file to store each frame
    logger.info("Entering the main drawing loop")
    total_frames = len(animation_params["dynamic_params"])
    with VideoWriter(args.path, resolution=args.resolution, fps=30) as vw:
        for index, curr_params in enumerate(animation_params["dynamic_params"]):
            logger.info(f"Rendering frame {index+1} / {total_frames}")
            # Load parameters for the current frame
            smpl_pose = np.array(curr_params["smpl_pose"])
            smpl_translation = np.array(curr_params["smpl_translation"])
            camera_quaternion = np.array(curr_params["camera_quaternion"])
            camera_translation = np.array(curr_params["camera_translation"])
            # Update the SMPL mesh for the current pose
            smpl_vertices = smpl_model.get_smpl(smpl_pose, smpl_translation)
            smpl_mesh.update_vertices(smpl_vertices)
            # Set the current camera position
            camera.set_position(camera_quaternion, camera_translation)
            # Render the scene to temporary image
            scene.render(tmp_frame_path, use_gpu=not args.cpu, samples=args.n_samples)
            # Read the resulting frame back
            img = imread(tmp_frame_path)
            # Frames have transparent background; perform an alpha blending with white background instead
            img_white_bkg = blend_with_background(img, (1.0, 1.0, 1.0))
            # Add the frame to the video
            vw.write(img_white_bkg)
    # Clean up
    os.remove(tmp_frame_path)
    logger.info("Rendering complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Blendify example 05: SMPL movement.")

    # Paths to output files
    parser.add_argument("-p", "--path", type=str, default="./05_smpl_movement.mp4",
                        help="Path to the resulting video")
    parser.add_argument("-o", "--output-blend", type=str, default=None,
                        help="Path to the resulting blend file")

    # Rendering parameters
    parser.add_argument("-n", "--n-samples", default=128, type=int,
                        help="Number of paths to trace for each pixel in the render (default: 256)")
    parser.add_argument("-res", "--resolution", default=(1280, 720), nargs=2, type=int,
                        help="Rendering resolution, (default: (1280, 720))")
    parser.add_argument("--cpu", action="store_true",
                        help="Use CPU for rendering (by default GPU is used)")
    parser.add_argument("-sk", "--skip_download", action="store_true",
                        help="Skip asset downloads")

    arguments = parser.parse_args()


    def download(fileurl, filename):
        progress_report = lambda block_num, block_size, total_size: print(
            f"Downloading {filename}: {block_num * block_size / 2 ** 20:.2f}/{total_size / 2 ** 20:.2f}MB", end="\r")
        if not os.path.isfile(filename) or request.urlopen(fileurl).length != os.stat(filename).st_size:
            request.urlretrieve(fileurl, filename, progress_report)
            print()


    # Downloading assets if needed
    if not arguments.skip_download:
        os.makedirs("assets/05_smpl_movement", exist_ok=True)
        download("https://nextcloud.mpi-klsb.mpg.de/index.php/s/AESiBaXXyagNmrE/download",
                 "assets/05_smpl_movement/scene_texture.jpg")
        download("https://nextcloud.mpi-klsb.mpg.de/index.php/s/QCjTsJqSSrNb5nJ/download",
                 "assets/05_smpl_movement/scene_mesh.ply")
        download("https://nextcloud.mpi-klsb.mpg.de/index.php/s/dNtecaSTPkYoKey/download",
                 "assets/05_smpl_movement/scene_face_uvmap.npy")
        download("https://nextcloud.mpi-klsb.mpg.de/index.php/s/a2SYDcoPc5FoCwe/download",
                 "assets/05_smpl_movement/animation_data.json")

    main(arguments)
