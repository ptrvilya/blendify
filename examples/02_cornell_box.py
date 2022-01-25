import argparse

import numpy as np

import blendify
from blendify.renderables.materials import PrinsipledBSDFMaterial, GlossyBSDFMaterial
from blendify.renderables.colors import UniformColors


def main(args):
    scene = blendify.get_scene()
    scene.attach_blend("./examples/02_assets/cornell_box.blend")

    scene.add_perspective_camera(
        args.resolution, fov_x=np.deg2rad(39.1), quaternion=(-0.707, -0.707, 0.0, 0.0),
        translation=[-0.278, -0.800, 0.273]
    )

    scene.lights.add_area(
        shape="square", size=5, strength=40, cast_shadows=False,
        quaternion=(-0.707, -0.707, 0.0, 0.0), translation=[-0.278, -1, 0.273]
    )

    # Sphere 1
    sphere_1_material = PrinsipledBSDFMaterial(
        specular=0.5,
        sheen=0.0,
        sheen_tint=0.4,
        ior=1.46,
        transmission=1.0,
        transmission_roughness=0.0,
        alpha=0.7,
        clearcoat=1.0,
        clearcoat_roughness=0.0,
    )
    sphere_1_color = UniformColors((1.0, 153/255, 102/255))
    sphere_1 = scene.renderables.add_sphere_nurbs(
        0.08, sphere_1_material, sphere_1_color, translation=[-0.22, 0.05, 0.08]
    )

    # Sphere 2
    sphere_2_material = PrinsipledBSDFMaterial(
        metallic=1.0,
        specular=0.5,
        roughness=0.07,
        sheen_tint=0.4,
        clearcoat=0.2,
        clearcoat_roughness=0.4
    )
    sphere_2_color = UniformColors((1.0, 1.0, 1.0))
    sphere_2 = scene.renderables.add_sphere_nurbs(
        0.08, sphere_2_material, sphere_2_color, translation=[-0.12, 0.25, 0.08]
    )

    # Cylinder
    cylinder_material = GlossyBSDFMaterial(
        roughness=0.5
    )
    cylinder_color = UniformColors((102/255, 102/255, 1.0))
    cylinder = scene.renderables.add_cylinder_mesh(
        0.08, 0.3, cylinder_material, cylinder_color, translation=[-0.32, 0.25, 0.15]
    )

    # Circle
    circle_material = PrinsipledBSDFMaterial(
        metallic=1.0,
        specular=0.5,
        roughness=0.05,
        sheen_tint=0.8,
        clearcoat=0.8,
        clearcoat_roughness=0.1
    )
    circle_color = UniformColors((1.0, 1.0, 1.0))
    circle = scene.renderables.add_circle_mesh(
        0.17, circle_material, circle_color,
        quaternion=[0.720, 0.262, 0.604, -0.220], translation=[-0.43, 0.32, 0.18]
    )

    if args.blend is not None:
        scene.export(args.blend)
    scene.render(filepath=args.path, use_gpu=not args.cpu, samples=args.n_samples)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Blendify 02 example: Cornell Box.")

    parser.add_argument("-p", "--path", type=str, default="./02_cornell_box.png",
                        help="Path to the resulting image.")
    parser.add_argument("-b", "--blend", type=str, default=None,
                        help="Path to the resulting blend file.")
    parser.add_argument("-n", "--n-samples", default=2048, type=int)
    parser.add_argument("--resolution", default=(1024, 1024), nargs=2, type=int,
                        help="Rendering resolution, (default: (1024, 1024)).")
    parser.add_argument("--cpu", action="store_true", help="Use CPU for rendering")

    arguments = parser.parse_args()
    main(arguments)
