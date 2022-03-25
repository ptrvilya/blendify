import argparse

import numpy as np

import blendify
from blendify.renderables.colors import UniformColors
from blendify.renderables.materials import PrinsipledBSDFMaterial


def main(args):
    # Create scene
    scene = blendify.get_scene()
    # Add camera to the scene
    scene.set_perspective_camera(resolution=args.resolution, focal_dist=640)
    # Create one material for all objects
    material = PrinsipledBSDFMaterial()
    # Create separate colors for each objects
    colors_sphere = UniformColors((0.3, 0, 0.9))
    colors_circle = UniformColors((0.5, 0.3, 0.9))
    colors_cylinder = UniformColors((0.0, 0.9, 0.9))
    colors_curve = UniformColors((1., 0., 0.2))
    # Add primitives to the scene
    sphere = scene.renderables.add_sphere_nurbs(1, material, colors_sphere)
    circle = scene.renderables.add_circle_mesh(0.7, material, colors_circle)
    cylinder = scene.renderables.add_cylinder_mesh(1.3, 2.3, material, colors_cylinder)
    keypoints = np.array([[1, 0, 0.], [-1, 0, 0], [0, -2, -4], [-1, -3, -6]])
    curve = scene.renderables.add_curve_nurbs(keypoints, 0.1, material, colors_curve)
    # Translate objects
    cylinder.translation = cylinder.translation + np.array([1, 1, -8])
    circle.translation = circle.translation + np.array([0, 1, -4.5])
    sphere.translation = sphere.translation + np.array([0, 0, -4.5])
    # Add light to the scene
    light = scene.lights.add_sun(strength=5)
    # Optionally save blend file with the scene
    if args.output_blend is not None:
        scene.export(args.output_blend)
    # Render the scene
    scene.render(filepath=args.path, use_gpu=not args.cpu, samples=args.n_samples, save_depth=True, save_albedo=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Blendify 06 example: NURBS Primitives Rendering.")

    # Paths to output files
    parser.add_argument("-p", "--path", type=str, default="./results/06_nurbs_primitives_render.png",
                        help="Path to the resulting image.")
    parser.add_argument("-o", "--output-blend", type=str, default=None,
                        help="Path to the resulting blend file.")

    # Rendering parameters
    parser.add_argument("-n", "--n-samples", default=256, type=int,
                        help="Number of paths to trace for each pixel in the render (default: 256)")
    parser.add_argument("-res", "--resolution", default=(1280, 720), nargs=2, type=int,
                        help="Rendering resolution, (default: (1280, 720))")
    parser.add_argument("--cpu", action="store_true",
                        help="Use CPU for rendering (by default GPU is used)")

    arguments = parser.parse_args()
    main(arguments)
