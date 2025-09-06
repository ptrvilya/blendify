import argparse
import bpy
import numpy as np
import trimesh
from videoio import VideoWriter
from loguru import logger

from blendify import scene
from blendify.colors import UniformColors, VertexColors
from blendify.materials import PrincipledBSDFMaterial
from blendify.utils.camera_trajectory import Trajectory
from blendify.utils.pointcloud import estimate_normals_from_pointcloud, approximate_colors_from_camera


def main(args):
    # Attach blender file with scene (walls and floor)
    logger.info("Attaching blend to the scene")
    scene.attach_blend("./assets/light_box.blend")
    # Set custom parameters to improve quality of rendering
    bpy.context.scene.cycles.max_bounces = 30
    bpy.context.scene.cycles.transmission_bounces = 20
    bpy.context.scene.cycles.transparent_max_bounces = 15
    bpy.context.scene.cycles.diffuse_bounces = 10
    # Interpolation of the camera trajectory
    # Start, middle and end points of the camera trajectory
    left_translation, left_rotation = \
        np.array([-0.5, -6.5, 2.4], dtype=np.float32), np.array([0.866, 0.5, 0.0, 0.0], dtype=np.float32)
    middle_translation, middle_rotation = \
        np.array([4, -6.5, 2.4], dtype=np.float32), np.array([0.793, 0.505, 0.184, 0.288], dtype=np.float32)
    right_translation, right_rotation = \
        np.array([6.5, -0.7, 2.4], dtype=np.float32), np.array([0.612, 0.354, 0.354, 0.612], dtype=np.float32)
    # Interpolate camera trajectory
    logger.info("Creating camera and interpolating its trajectory")
    camera_trajectory = Trajectory()
    camera_trajectory.add_keypoint(quaternion=left_rotation, position=left_translation, time=0)
    camera_trajectory.add_keypoint(quaternion=middle_rotation, position=middle_translation, time=2.5)
    camera_trajectory.add_keypoint(quaternion=right_rotation, position=right_translation, time=5)
    camera_trajectory = camera_trajectory.refine_trajectory(time_step=1/30, smoothness=5.0)
    # Add camera to the scene (position will be set in the rendering loop)
    camera = scene.set_perspective_camera(
        resolution=args.resolution, fov_x=np.deg2rad(73)
    )

    # Add lights to the scene
    logger.info("Setting up the Blender scene")
    scene.lights.add_point(rotation=(0.571, 0.169, 0.272, 0.756), translation=(21.0, 0.0, 7.0), strength=8000)
    scene.lights.add_point(rotation=(0.571, 0.169, 0.272, 0.756), translation=(0.0, -21, 7.0), strength=8000)

    # Camera colored PointCloud
    # source of the mesh https://graphics.stanford.edu/data/3Dscanrep/
    # load only vertices of the example mesh
    mesh = trimesh.load("./assets/bunny.ply", process=False, validate=False)
    vertices = mesh.vertices
    # estimate normals
    if args.backend == "orig":
        normals = np.array(mesh.vertex_normals)
    else:
        normals = estimate_normals_from_pointcloud(vertices, backend=args.backend, device="cpu" if args.cpu else "cuda")
    # create material
    poincloud_material = PrincipledBSDFMaterial(specular_ior=0.5)
    # create default color (will be changed in the rendering loop)
    pointcloud_colors_init = UniformColors((51/255, 204/255, 204/255))
    # add pointcloud to the scene
    pointcloud = scene.renderables.add_pointcloud(
        vertices=vertices, material=poincloud_material, colors=pointcloud_colors_init, point_size=0.03,
        particle_emission_strength=0.05, rotation=(1, 0, 0, 0), translation=(0, 0, 0)
    )

    # Optionally save blend file with the scene at frame 0
    if args.output_blend is not None:
        scene.export(args.output_blend)

    # Render the video frame by frame
    logger.info("Entering the main drawing loop")
    total_frames = len(camera_trajectory)
    with VideoWriter(args.path, resolution=args.resolution, fps=30) as vw:
        for index, position in enumerate(camera_trajectory):
            logger.info(f"Rendering frame {index:03d} / {total_frames:03d}")
            # Set new camera position
            camera.set_position(rotation=position["quaternion"], translation=position["position"])
            # Approximate colors from normals and camera_view_direction
            camera_viewdir = camera.get_camera_viewdir()
            per_vertex_recolor = approximate_colors_from_camera(
                camera_viewdir, normals, per_vertex_color=pointcloud_colors_init.color, back_color=(0.0, 0.0, 0.0, 0.0)
            )
            # Create VertexColor instance and set it to the PointCloud
            pointcloud_colors_new = VertexColors(per_vertex_recolor)
            pointcloud.update_colors(pointcloud_colors_new)
            # Render the scene to temporary image
            img = scene.render(use_gpu=not args.cpu, samples=args.n_samples)
            # Read the resulting frame back
            # Frames have transparent background; perform an alpha blending with white background instead
            alpha = img[:, :, 3:4].astype(np.int32)
            img_white_bkg = ((img[:, :, :3] * alpha + 255 * (255 - alpha)) // 255).astype(np.uint8)
            # Add the frame to the video
            vw.write(img_white_bkg)
    logger.info("Rendering complete")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Blendify example 04: Camera colored PointCloud.")

    # Paths to output files
    parser.add_argument("-p", "--path", type=str, default="./04_camera_colored_point_cloud.mp4",
                        help="Path to the resulting video")
    parser.add_argument("-o", "--output-blend", type=str, default=None,
                        help="Path to the resulting blend file")

    # Rendering parameters
    parser.add_argument("-n", "--n-samples", default=256, type=int,
                        help="Number of paths to trace for each pixel in the render (default: 256)")
    parser.add_argument("-res", "--resolution", default=(1024, 1024), nargs=2, type=int,
                        help="Rendering resolution, (default: (1024, 1024))")
    parser.add_argument("--cpu", action="store_true",
                        help="Use CPU for rendering (by default GPU is used)")

    # Other parameters
    parser.add_argument("-b", "--backend", type=str, default="orig", choices=["orig", "open3d", "pytorch3d"],
                        help="Backend to use for normal estimation. Orig corresponds to original mesh normals, "
                             "i.e. no estimation is performed (default: orig)")

    arguments = parser.parse_args()
    main(arguments)
