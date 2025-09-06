import argparse
from zipfile import ZipFile
from io import BytesIO

import numpy as np
import trimesh

from blendify import scene
from blendify.colors import UniformColors, VertexUV, FileTextureColors
from blendify.materials import  PrincipledBSDFMaterial


def load_donut_mesh(path_to_zip: str):
    donut_file = BytesIO(ZipFile(path_to_zip).read("donut.obj"))
    mesh = trimesh.load(donut_file, "obj", process=False, group_material=True, mantain_order=True)
    # Create accumulated mesh
    offset_v, offset_f = 0, 0
    vertices, faces, uv_map, faces_material = [], [], [], []
    for obj_ind, obj_key in enumerate(mesh.geometry.keys()):
        # Select object from the TriMesh scene
        obj_vertices, obj_faces = mesh.geometry[obj_key].vertices, mesh.geometry[obj_key].faces
        # Accumulate vertices and faces
        vertices.append(np.asarray(obj_vertices))
        faces.append(np.asarray(obj_faces) + offset_v)
        # Accumulate face indexes for per-face materials
        faces_material.append(np.full(len(obj_faces), fill_value=obj_ind, dtype=int))
        # Accumulate UV map
        visual_kind = mesh.geometry[obj_key].visual.kind
        if visual_kind is not None and visual_kind == "texture":
            uv_map.append(mesh.geometry[obj_key].visual.uv)
        else:
            uv_map.append(np.zeros((len(obj_vertices), 2), dtype=np.float32))
        # Accumulate offsets for vertices and faces
        offset_v += len(obj_vertices)
        offset_f += len(obj_faces)
    vertices = np.concatenate(vertices)
    faces = np.concatenate(faces)
    faces_material = np.concatenate(faces_material)
    uv_map = np.concatenate(uv_map)

    return vertices, faces, uv_map, faces_material


def main(args):
    # Load mesh
    vertices, faces, uv_map, faces_material = load_donut_mesh("./assets/donut.obj.zip")
    # Create per-part materials and colors
    # Base and Icing have uniform colors
    material_base = PrincipledBSDFMaterial(roughness=0.4, coat_roughness=0.03)
    material_icing = PrincipledBSDFMaterial(roughness=0.545, coat_ior=0.1, coat_roughness=0.03)
    colors_base = UniformColors((0.7, 0.4, 0.1))
    colors_icing = UniformColors((0.9, 0.58, 0.72))
    # Sprinkles have texture colors to allow per-sprinkle coloring
    material_sprinkles = PrincipledBSDFMaterial(roughness=0.894, coat_roughness=0.03)
    vertex_uv_map = VertexUV(uv_map)
    colors_sprinkles = FileTextureColors("./assets/donut_sprinkles.png", vertex_uv_map)
    # Add mesh to the scene
    mesh_plastic = scene.renderables.add_mesh(
        vertices, faces,
        faces_material=faces_material,
        material=[material_sprinkles, material_icing, material_base],
        colors=[colors_sprinkles, colors_icing, colors_base]
    )
    mesh_plastic.set_smooth(True)
    # Set camera
    scene.set_perspective_camera(
        args.resolution, fov_x=np.deg2rad(20.8),
        translation=(0, -0.56, 0.43),
        rotation=(0.889, 0.458, 0, 0),
    )
    # Set lights
    scene.lights.set_background_light(0.01)
    scene.lights.add_point(strength=25, shadow_soft_size=0.1, translation=(-0.3, 1.0, 0.7))
    scene.lights.add_point(strength=25, shadow_soft_size=0.1, translation=(1.1, 0.13, 0.6))
    scene.lights.add_point(strength=25, shadow_soft_size=0.1, translation=(-0.1, -1.1, 1.2))
    # Render the scene
    scene.render(filepath=args.path, use_gpu=not args.cpu, samples=args.n_samples)
    # Optionally save blend file with the scene
    if args.output_blend is not None:
        scene.export(args.output_blend)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Blendify example 08: Render mesh with per-face material.")

    # Paths to output files
    parser.add_argument("-p", "--path", type=str, default="./08_per_face_material.png",
                        help="Path to the resulting image")
    parser.add_argument("-o", "--output-blend", type=str, default=None,
                        help="Path to the resulting blend file")

    # Rendering parameters
    parser.add_argument("-n", "--n-samples", default=256, type=int,
                        help="Number of paths to trace for each pixel in the render (default: 256)")
    parser.add_argument("-res", "--resolution", default=(1920, 1920), nargs=2, type=int,
                        help="Rendering resolution, (default: (1920, 1920))")
    parser.add_argument("--cpu", action="store_true",
                        help="Use CPU for rendering (by default GPU is used)")

    arguments = parser.parse_args()
    main(arguments)
