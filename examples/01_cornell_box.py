import argparse

import numpy as np

from blendify import scene
from blendify.colors import UniformColors
from blendify.materials import PrincipledBSDFMaterial, GlossyBSDFMaterial


def main(args):
    # Attach blender file with scene (walls, floor and ceiling)
    scene.attach_blend("./assets/cornell_box.blend")
    # Add camera to the scene
    scene.set_perspective_camera(
        args.resolution, fov_x=np.deg2rad(39.1), rotation=(-0.707, -0.707, 0.0, 0.0),
        translation=[-0.278, -0.800, 0.273]
    )
    # Add light to the scene
    scene.lights.add_area(
        shape="square", size=5, strength=40, use_shadow=False,
        rotation=(-0.707, -0.707, 0.0, 0.0), translation=[-0.278, -1, 0.273]
    )
    # Fill up the scene with objects
    # Add Sphere 1
    sphere_1_material = PrincipledBSDFMaterial(
        specular_ior=0.5,
        sheen_weight=0.0,
        sheen_roughness=0.4,
        ior=1.46,
        transmission_weight=1.0,
        alpha=0.7,
        coat_ior=1.0,
        coat_roughness=0.0,
    )
    sphere_1_color = UniformColors((1.0, 153/255, 102/255))
    sphere_1 = scene.renderables.add_sphere_nurbs(
        0.08, sphere_1_material, sphere_1_color, translation=[-0.22, 0.05, 0.08]
    )
    # Add Sphere 2
    sphere_2_material = PrincipledBSDFMaterial(
        metallic=1.0,
        specular_ior=0.5,
        roughness=0.07,
        sheen_roughness=0.4,
        coat_ior=0.2,
        coat_roughness=0.4
    )
    sphere_2_color = UniformColors((1.0, 1.0, 1.0))
    sphere_2 = scene.renderables.add_sphere_nurbs(
        0.08, sphere_2_material, sphere_2_color, translation=[-0.12, 0.25, 0.08]
    )
    # Add Cylinder
    cylinder_material = GlossyBSDFMaterial(
        roughness=0.5
    )
    cylinder_color = UniformColors((102/255, 102/255, 1.0))
    cylinder = scene.renderables.add_cylinder_mesh(
        0.08, 0.3, cylinder_material, cylinder_color, translation=[-0.32, 0.25, 0.15]
    )
    # Add Circle
    circle_material = PrincipledBSDFMaterial(
        metallic=1.0,
        specular_ior=0.5,
        roughness=0.05,
        sheen_roughness=0.8,
        coat_ior=0.8,
        coat_roughness=0.1
    )
    circle_color = UniformColors((1.0, 1.0, 1.0))
    circle = scene.renderables.add_circle_mesh(
        0.17, circle_material, circle_color,
        rotation=[0.720, 0.262, 0.604, -0.220], translation=[-0.43, 0.32, 0.18]
    )
    # Render the scene
    scene.render(filepath=args.path, use_gpu=not args.cpu, samples=args.n_samples, use_denoiser=True)
    # Optionally save blend file with the scene
    if args.output_blend is not None:
        scene.export(args.output_blend)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Blendify example 01: Cornell Box.")

    # Paths to output files
    parser.add_argument("-p", "--path", type=str, default="./01_cornell_box.png",
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
