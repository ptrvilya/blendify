import argparse

import numpy as np
from videoio import VideoWriter
from loguru import logger

from blendify import scene
from blendify.colors import UniformColors
from blendify.materials import PrincipledBSDFMaterial
from blendify.utils.image import blend_with_background


def circle_points(radius=1, count=100, angle_shift=np.pi / 4):
    angle_step = 2 * np.pi / count
    angles = np.arange(count) * angle_step + angle_shift
    coords = np.stack([np.cos(angles), np.sin(angles), np.zeros(count)], axis=-1) * radius
    return coords


def line_points(line_start, line_end, count=10, include_endpoints=False):
    line_vct = line_end - line_start
    line_len = np.linalg.norm(line_vct)
    line_vct_norm = line_vct / line_len
    len_vals = np.linspace(0, line_len, count + (2 if not include_endpoints else 0), endpoint=True)
    if not include_endpoints:
        len_vals = len_vals[1:-1]
    line_dirs = line_vct_norm[None, :] * len_vals[:, None]
    coords = line_start[None, :] + line_dirs
    return coords


def main(args):
    # Add camera to the scene
    scene.set_perspective_camera(resolution=args.resolution, focal_dist=640, rotation=(0.983, 0.182, 0, 0),
                                 translation=(0, -1.15, -1.54))
    # Create one material for all objects
    material = PrincipledBSDFMaterial()

    # Create infinity symbol; for that, we need to generate a circle, split it in half and connect halves with lines
    figure_center = np.array([0, 0., -4])
    figure_size = np.array([4., 1., 0.1])
    circle_kp_count = 100
    line_kp_count = 30
    circle_kp = circle_points(figure_size[1], count=circle_kp_count)
    circle_kp = circle_kp + figure_center[None, :]
    left_part = circle_kp[:3 * circle_kp_count // 4]
    right_part = np.vstack([circle_kp[circle_kp_count // 2:], circle_kp[0:circle_kp_count // 4]])
    halves_distance = figure_size[0] - figure_size[1]
    left_part = left_part + np.array([[-halves_distance / 2, 0., 0.]])
    right_part = right_part + np.array([[halves_distance / 2, 0., 0.]])
    # Add height difference between points
    height_diffs = np.linspace(-figure_size[2] / 2., figure_size[2] / 2., len(left_part))
    height_diffs = np.hstack([np.zeros((len(left_part), 2)), height_diffs[:, None]])
    left_part = left_part + height_diffs
    right_part = right_part + height_diffs

    # Connect two parts with lines and combine all the keypoints into the single figure
    line1_kp = line_points(left_part[-1], right_part[-1], count=line_kp_count)
    line2_kp = line_points(right_part[0], left_part[0], count=line_kp_count)
    infinity_figure_kp = np.vstack([left_part, line1_kp, right_part[::-1], line2_kp])

    # Create spheres on keypoints
    sphere_color = UniformColors((0.33, 1.0, 0.1))
    for kp in infinity_figure_kp:
        sphere = scene.renderables.add_sphere_nurbs(radius=0.03, material=material,
                                                    colors=sphere_color, translation=kp)

    # Create curve in motion
    curve_len_in_kp = 100
    curr_kp_offset = 0
    total_frames = len(infinity_figure_kp)
    curve_color = UniformColors((1., 0.5, 0))
    curve = None

    light = scene.lights.add_sun(strength=3)
    # Optionally save blend file with the scene
    if args.output_blend is not None:
        scene.export(args.output_blend)

    # Render the scene
    with VideoWriter(args.path, resolution=args.resolution, fps=args.fps) as vw:
        for index in range(total_frames):
            logger.info(f"Rendering frame {index + 1} / {total_frames}")
            # Build current curve trajectory
            trajectory_kp = infinity_figure_kp[curr_kp_offset:curr_kp_offset + curve_len_in_kp]
            loop_kp_count = curr_kp_offset + curve_len_in_kp - len(infinity_figure_kp)
            if loop_kp_count > 0:
                trajectory_kp = np.vstack([trajectory_kp, infinity_figure_kp[:loop_kp_count]])
            if curve is not None:
                scene.renderables.remove(curve)
            curve = scene.renderables.add_curve_nurbs(trajectory_kp, 0.04, material, curve_color)
            # Render the scene to temporary image
            img = scene.render(use_gpu=not args.cpu, samples=args.n_samples)
            # Frames have transparent background; perform an alpha blending with white background instead
            img_with_bkg = blend_with_background(img, (1.0, 1.0, 1.0))
            # Add the frame to the video
            vw.write(img_with_bkg)
            # Shift the curve
            curr_kp_offset += 1
            if curr_kp_offset >= len(infinity_figure_kp):
                curr_kp_offset = 0
    logger.info("Rendering complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Blendify example 06: NURBS Trajectory Rendering.")

    # Paths to output files
    parser.add_argument("-p", "--path", type=str, default="./06_nurbs_trajectory.mp4",
                        help="Path to the resulting image.")
    parser.add_argument("-o", "--output-blend", type=str, default=None,
                        help="Path to the resulting blend file.")

    # Rendering parameters
    parser.add_argument("-n", "--n-samples", default=256, type=int,
                        help="Number of paths to trace for each pixel in the render (default: 256)")
    parser.add_argument("-res", "--resolution", default=(1280, 720), nargs=2, type=int,
                        help="Rendering resolution, (default: (1280, 720))")
    parser.add_argument("--fps", default=30, type=int,
                        help="FPS of the resulting video (default: 30)")
    parser.add_argument("--cpu", action="store_true",
                        help="Use CPU for rendering (by default GPU is used)")

    arguments = parser.parse_args()
    main(arguments)
