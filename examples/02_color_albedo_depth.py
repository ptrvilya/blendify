import argparse

import numpy as np
import trimesh

from blendify import scene
from blendify.colors import UniformColors
from blendify.materials import PrincipledBSDFMaterial


def main(args):
    # Add camera to the scene
    scene.set_perspective_camera(args.resolution, focal_dist=1250)
    # Load mesh
    mesh = trimesh.load("./assets/knot.obj", process=False)
    vertices, faces, uv = np.array(mesh.vertices), np.array(mesh.faces), np.array(mesh.visual.uv)
    # Add mesh with uniform color to the scene
    material = PrincipledBSDFMaterial()
    colors = UniformColors((0.3, 0, 0.9))
    mesh = scene.renderables.add_mesh(vertices, faces, material=material, colors=colors)
    # Translate the mesh to better fit the camera frame
    mesh.translation = mesh.translation + np.array([1.2, 0, -4.5])
    # Add light to the scene
    light = scene.lights.add_sun(strength=5)
    # Optionally save blend file with the scene
    if args.output_blend is not None:
        scene.export(args.output_blend)
    # Render the scene
    scene.render(filepath=args.path, use_gpu=not args.cpu, samples=args.n_samples, save_depth=True, save_albedo=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Blendify example 02: Render mesh with albedo and depth.")

    # Paths to output files
    parser.add_argument("-p", "--path", type=str, default="./02_color_albedo_depth.png",
                        help="Path to the resulting image")
    parser.add_argument("-o", "--output-blend", type=str, default=None,
                        help="Path to the resulting blend file")

    # Rendering parameters
    parser.add_argument("-n", "--n-samples", default=256, type=int,
                        help="Number of paths to trace for each pixel in the render (default: 256)")
    parser.add_argument("-res", "--resolution", default=(1024, 1024), nargs=2, type=int,
                        help="Rendering resolution, (default: (1024, 1024))")
    parser.add_argument("--cpu", action="store_true",
                        help="Use CPU for rendering (by default GPU is used)")

    arguments = parser.parse_args()
    main(arguments)
