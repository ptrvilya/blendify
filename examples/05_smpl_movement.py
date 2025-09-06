import argparse
import json
import os
import numpy as np
import trimesh
import tempfile
import zipfile
from urllib import request
from loguru import logger
from videoio import VideoWriter

from blendify import scene
from blendify.colors import UniformColors, FacesUV, FileTextureColors
from blendify.materials import PrincipledBSDFMaterial
from blendify.utils.image import blend_with_background
from blendify.utils.smpl_wrapper import SMPLWrapper


def main(args):
    # Load the scene
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
    # Please refer to https://github.com/vchoutas/smplx#loading-smpl-x-smplh-and-smpl
    # for details on SMPL model setup
    if os.path.isdir(os.path.join(args.smpl_path, 'smpl')):
        smpl_model = SMPLWrapper(smpl_root=args.smpl_path,
                             gender=animation_params["static_params"]["smpl_gender"],
                             shape_params=animation_params["static_params"]["smpl_shape"])
    else:
        logger.error(f"Could not find SMPL model files in {args.smpl_path}. Please refer to "
                     f"https://github.com/vchoutas/smplx#loading-smpl-x-smplh-and-smpl "
                     "for details on SMPL model setup and provide the path to the root folder containing SMPL model files with -s flag.")
        return

    logger.info("Setting up the Blender scene")

    # Add the camera
    camera = scene.set_perspective_camera(args.resolution, fov_y=np.deg2rad(75))

    # Define the materials
    # Material and Colors for SMPL mesh
    smpl_material = PrincipledBSDFMaterial()
    smpl_colors = UniformColors((0.3, 0.3, 0.3))
    # Material and Colors for background scene mesh
    scene_mesh_material = PrincipledBSDFMaterial()
    scene_mesh_material.specular_ior = 1.0
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
        strength=2.3, rotation_mode="euleryz", rotation=(-45, -90)
    )
    sunlight2 = scene.lights.add_sun(
        strength=3, rotation_mode="euleryz", rotation=(-45, 165)
    )
    sunlight2.use_shadow = False

    # Optionally save blend file with the scene at frame 0
    if args.output_blend is not None:
        scene.export(args.output_blend)

    # Rendering loop
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
            camera.set_position(rotation=camera_quaternion, translation=camera_translation)
            # Render the scene to temporary image
            img = scene.render(use_gpu=not args.cpu, samples=args.n_samples)
            # Frames have transparent background; perform an alpha blending with white background instead
            img_white_bkg = blend_with_background(img, (1.0, 1.0, 1.0))
            # Add the frame to the video
            vw.write(img_white_bkg)
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

    # Additional parameters
    parser.add_argument("-s", "--smpl-path", type=str, default="data/smplx_data",
                        help="Path to SMPL/SMPLX model files.")

    arguments = parser.parse_args()


    def download_zipped(file_url, target_dir):
        progress_report = lambda block_num, block_size, total_size: print(
            f"Downloading data: {block_num * block_size / 2 ** 20:.2f}/{total_size / 2 ** 20:.2f}MB", end="\r")
        if not os.path.isdir(target_dir):
            with tempfile.TemporaryDirectory() as tmpdirname:
                # Download the zipped file to a temporary directory
                request.urlretrieve(file_url, os.path.join(tmpdirname, "data.zip"), progress_report)
                print()
                os.makedirs(target_dir)
                # Unzip the file to the target directory
                logger.info("Extracting the data")
                with zipfile.ZipFile(os.path.join(tmpdirname, "data.zip"), 'r') as zip_ref:
                    zip_ref.extractall(target_dir)
        else:
            logger.info(f"Assets folder {target_dir} exist, skipping download.")


    # Downloading assets if needed
    if not arguments.skip_download:
        # The scene mesh was generated from HPS dataset (MPI_Etage6 pointcloud) using blendify.utils.pointcloud.meshify_pc_from_file
        download_zipped("https://github.com/ptrvilya/blendify/releases/download/v2.0.1/05_smpl_movement_assets.zip",
                 "assets/05_smpl_movement")

    main(arguments)
