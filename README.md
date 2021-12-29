Minimal scene example
```
import numpy as np

from blendify import get_scene
from blendify.cameras import PerspectiveCamera
from blendify.renderables.materials import PrinsipledBSDFMaterial
from blendify.renderables.colors import UniformColors

scene = get_scene()
scene.lights.add_point(quaternion=(0.571, 0.169, 0.272, 0.756), translation=(4.07, 1.0, 5.9), strength=1000)
camera = PerspectiveCamera((1920, 1080), 40, fov_x=np.deg2rad(70), quaternion=(0.780, 0.484, 0.209, 0.337), translation=(7.36, -6.93, 4.96))
scene.camera = camera

verts = np.load("examples/verts.npy")
faces = np.load("examples/faces.npy")

material = PrinsipledBSDFMaterial()
color = UniformColors((1.0, 0.0, 0.0))
scene.renderables.add_mesh(verts, faces, material, color)
scene.render(use_gpu=False, samples=64)
```