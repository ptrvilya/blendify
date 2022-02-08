import numpy as np
import blendify
from skimage.io import imread
from blendify.cameras import PerspectiveCamera
from blendify.renderables.materials import PrinsipledBSDFMaterial
from blendify.renderables.colors import FileTextureColors, TextureColors

scene = blendify.get_scene()
camera = PerspectiveCamera((1280, 720), focal_dist=640)
scene.camera = camera
vertices = np.load("verts.npy")
faces = np.load("faces.npy")
uv_map = np.load("uv_map.npy")
material = PrinsipledBSDFMaterial()
img = imread("texture.jpg")
colors = TextureColors(img, uv_map)
mesh = scene.renderables.add_mesh(vertices, faces, material=material, colors=colors)
mesh.translation = mesh.translation + np.array([0, 0, -4.5])
light = scene.lights.add_sun(strength=5)
scene.render("test_texture.png")
