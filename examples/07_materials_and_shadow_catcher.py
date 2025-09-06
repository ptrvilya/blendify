import argparse

import numpy as np
import trimesh

from blendify import scene
from blendify.colors import UniformColors
from blendify.materials import MetalMaterial, PlasticMaterial, PrincipledBSDFMaterial, PlasticWireframeMaterial


def main(args):
    # Load mesh
    mesh = trimesh.load("./assets/lucy.ply", process=False)
    vertices, faces = np.array(mesh.vertices), np.array(mesh.faces)
    # 1. Add mesh with Plastic material to the scene
    material_plastic = PlasticMaterial()
    colors_plastic = UniformColors((0.64, 0.8, 0.96))
    mesh_plastic = scene.renderables.add_mesh(
        vertices, faces, material=material_plastic, colors=colors_plastic
    )
    mesh_plastic.set_smooth(True)
    # Translate the mesh
    mesh_plastic.translation = mesh_plastic.translation + np.array([2.0, 0, 0])
    # 2. Add mesh with Metal material to the scene
    material_metal = MetalMaterial()
    colors_metal = UniformColors((0.94, 0.62, 0.46))
    mesh_metal = scene.renderables.add_mesh(
        vertices, faces, material=material_metal, colors=colors_metal
    )
    mesh_metal.set_smooth(True)
    # 3. Add mesh with PrincipledBSDF + Wireframe material to the scene
    material_wireframe = PlasticWireframeMaterial(wireframe_thickness=0.0035)
    colors_wireframe = UniformColors((0.2, 1.0, 0.47))
    mesh_wireframe = scene.renderables.add_mesh(
        vertices, faces, material=material_wireframe, colors=colors_wireframe
    )
    mesh_wireframe.set_smooth(True)
    # Translate the mesh
    mesh_wireframe.translation = mesh_wireframe.translation + np.array([-2.0, 0, 0])
    # Add shadow catcher plane
    materials_plane = PrincipledBSDFMaterial()
    colors_plane = UniformColors((0.5, 0.5, 0.5))
    plane = scene.renderables.add_plane_mesh(
        25.0, shadow_catcher=True, material=materials_plane, colors=colors_plane,
    )
    # Translate to align with meshes' lowest point
    plane.translation = np.array([0, -4, vertices[:, 2].min() - 0.01])
    # Set camera
    scene.set_perspective_camera(
        args.resolution, fov_x=np.deg2rad(30),
        translation=(0.6, 13.5, 4.5),
        rotation_mode="look_at", rotation=mesh_metal
    )
    # Set lights
    scene.lights.set_background_light(0.03)
    scene.lights.add_point(
        strength=600, shadow_soft_size=1.0, translation=(4, 6, 5), use_shadow=False
    )
    scene.lights.add_spot(
        strength=250, spot_size=np.deg2rad(47.6), spot_blend=0.458,
        translation=(-1.5, 4.15, 5), rotation=(0.930, -0.321, -0.152, -0.093)
    )
    # Render the scene
    scene.render(filepath=args.path, use_gpu=not args.cpu, samples=args.n_samples)
    # Optionally save blend file with the scene
    if args.output_blend is not None:
        scene.export(args.output_blend)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Blendify example 07: Render with 3 materials and shadow catcher.")

    # Paths to output files
    parser.add_argument("-p", "--path", type=str, default="./07_materials_and_shadow_catcher.png",
                        help="Path to the resulting image")
    parser.add_argument("-o", "--output-blend", type=str, default=None,
                        help="Path to the resulting blend file")

    # Rendering parameters
    parser.add_argument("-n", "--n-samples", default=256, type=int,
                        help="Number of paths to trace for each pixel in the render (default: 256)")
    parser.add_argument("-res", "--resolution", default=(1920, 1080), nargs=2, type=int,
                        help="Rendering resolution, (default: (1920, 1080))")
    parser.add_argument("--cpu", action="store_true",
                        help="Use CPU for rendering (by default GPU is used)")

    arguments = parser.parse_args()
    main(arguments)
