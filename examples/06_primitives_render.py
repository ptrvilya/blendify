import numpy as np
import blendify
from blendify.cameras import PerspectiveCamera
from blendify.renderables.materials import PrinsipledBSDFMaterial
from blendify.renderables.colors import UniformColors

scene = blendify.get_scene()
camera = PerspectiveCamera((1280, 720), focal_dist=640)
scene.camera = camera
material = PrinsipledBSDFMaterial()
colors = UniformColors((0.3, 0, 0.9))
colors2 = UniformColors((0.5, 0.3, 0.9))
sphere = scene.renderables.add_sphere(1, material, colors)
circle = scene.renderables.add_circle(0.7, material, colors2)
cylinder = scene.renderables.add_cylinder(1.3, 2.3, material, UniformColors((0.0, 0.9, 0.9)))
keypoints = np.array([[1, 0, 0.], [-1, 0, 0], [0, -2, -4], [-1, -3, -6]])
curve = scene.renderables.add_curve(keypoints, 0.1, material, UniformColors((1., 0., 0.2)))
cylinder.translation = circle.translation + np.array([1, 1, -8])
circle.translation = circle.translation + np.array([0, 1, -4.5])
sphere.translation = sphere.translation + np.array([0, 0, -4.5])
light = scene.lights.add_sun(strength=5)
scene.render("test_prim.png", save_depth=True, save_albedo=True)
# scene.export("test_prim.blend")
