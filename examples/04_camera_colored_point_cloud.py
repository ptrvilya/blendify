import argparse

import numpy as np

import blendify
from blendify.renderables.materials import PrinsipledBSDFMaterial
from blendify.renderables.colors import UniformColors
from blendify.utils.pointcloud import estimate_normals_from_pointcloud


def main(args):
    scene = blendify.get_scene()
    scene.attach_blend("./examples/knot/light_box.blend")

    scene.add_perspective_camera(
        (1024, 1024), fov_x=np.deg2rad(73), quaternion=(0.821, 0.383, 0.179, 0.383),
        translation=(5, -5, 5)
    )

    scene.lights.add_point(quaternion=(0.571, 0.169, 0.272, 0.756), translation=(5.5, 0.0, 3.0), strength=800)
    scene.lights.add_point(quaternion=(0.571, 0.169, 0.272, 0.756), translation=(0.0, -5.5, 3.0), strength=800)

    # Camera colored PointCloud
    # load only vertices of the example mesh
    vertices = np.load("./examples/knot/verts.npy")
    # estimate normals
    normals = estimate_normals_from_pointcloud(vertices, backend=args.backend, device="cpu" if args.cpu else "cuda")
    poincloud_material = PrinsipledBSDFMaterial(
        specular=0.5
    )
    pointcloud_color = UniformColors((51/255, 204/255, 204/255))
    pointcloud = scene.renderables.add_camera_colored_pointcloud(
        vertices, normals, poincloud_material, pointcloud_color, point_size=0.05,
        back_color=(1.0, 0.0, 0.0), quaternion=(1, 0, 0, 0), translation=(0, 0, 0)
    )

    if args.output_blend is not None:
        scene.export(args.output_blend)
    scene.render(filepath=args.path, use_gpu=not args.cpu, samples=args.n_samples)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Blendify 04 example: Camera colored PointCloud.")

    parser.add_argument("-p", "--path", type=str, default="./04_example.png",
                        help="Path to the resulting image.")
    parser.add_argument("-b", "--backend", type=str, default="open3d", choices=["open3d", "pytorch3d"],
                        help="Backend to use for normal estimation.")
    parser.add_argument("-o", "--output-blend", type=str, default=None,
                        help="Path to the resulting blend file.")
    parser.add_argument("-n", "--n-samples", default=2048, type=int)
    parser.add_argument("--resolution", default=(1024, 1024), nargs=2, type=int,
                        help="Rendering resolution, (default: (1024, 1024)).")
    parser.add_argument("--cpu", action="store_true", help="Use CPU for rendering")

    arguments = parser.parse_args()
    main(arguments)
