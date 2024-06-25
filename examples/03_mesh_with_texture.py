import argparse

import numpy as np
import trimesh
from skimage.io import imread

from blendify import scene
from blendify.colors import VertexUV, TextureColors
from blendify.materials import PrincipledBSDFMaterial


def main(args):
    # Add camera to the scene
    scene.set_perspective_camera(resolution=args.resolution, focal_dist=1250)
    # Load mesh
    mesh = trimesh.load("./assets/knot.ply", process=False)
    vertices, faces, uv = np.array(mesh.vertices), np.array(mesh.faces), np.array(mesh.visual.uv)
    # Create UV map from uv coordinates
    uv_map = VertexUV(uv)
    # Create TextureColors with newly loaded texture
    img = imread("./assets/knot_texture.jpg")
    colors = TextureColors(img, uv_map)
    # Create material with default parameters
    material = PrincipledBSDFMaterial()
    # Add mesh to the scene
    mesh = scene.renderables.add_mesh(vertices, faces, material=material, colors=colors)
    # Translate the mesh to better fit the camera frame
    mesh.translation = mesh.translation + np.array([1.2, 0, -4.5])
    # Add light to the scene
    light = scene.lights.add_sun(strength=3.5)
    # Render the scene
    scene.render(filepath=args.path, use_gpu=not args.cpu, samples=args.n_samples)
    # Optionally save blend file with the scene
    if args.output_blend is not None:
        scene.export(args.output_blend)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Blendify example 03: Simple mesh with texture.")

    # Paths to output files
    parser.add_argument("-p", "--path", type=str, default="./03_mesh_with_texture.png",
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
