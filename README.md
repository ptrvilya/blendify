<!-- ![blendify Logo](.github/blendify_logo_dark_bg.png#gh-dark-mode-only) -->
<!-- ![blendify Logo](.github/blendify_logo_light_bg.png#gh-light-mode-only) -->
![blendify Logo](.github/blendify_logo_light_bg.png)

## Introduction

Blendify is a simple framework providing high-level API to create and render scenes with Blender directly from Python.

Key-features:


## Installation instructions


## Quick Start
Cube render
```python
import blendify
# Get scene
scene = blendify.get_scene()
# Add light
scene.lights.add_point(strength=1000, translation=(4, -2, 4))
# Add camera
scene.set_perspective_camera((512, 512), fov_x=0.7, quaternion=(0.82, 0.42, 0.18, 0.34), translation=(5, -5, 5))
# Create material
material = blendify.renderables.materials.PrinsipledBSDFMaterial()
# Create color
color = blendify.renderables.colors.UniformColors((0.0, 1.0, 0.0))
# Add cube mesh
scene.renderables.add_cube_mesh(1.0, material, color)
# Render scene
scene.render(filepath="cube.jpg")
```


## Examples
<table>
  <tr align="center">
    <td><a href="examples/01_cornell_box.py"><b>Cornell Box</b></a></td>
    <td><a href="examples/02_color_albedo_depth.py"><b>Color, albedo and depth</b></a></td>
    <td><a href="examples/03_mesh_with_texture.py"><b>Mesh with texture</b></a></td>
  </tr>
  <tr align="center">
    <td>
      <img src=".github/01_cornell_box.jpg" width="1024px"/>
    </td>
    <td>
      <img src=".github/02_color_albedo_depth.jpg" width="1024px"/>
    </td>
    <td>
      <img src=".github/03_mesh_with_texture.jpg" width="1024px"/>
    </td>
  </tr>
  <tr align="center">
    <td><a href="examples/04_camera_colored_point_cloud.py"><b>Camera colored point cloud</b></a></td>
    <td><a href="examples/05_smpl_movement.py"><b>SMPL movement</b></a></td>
    <td><a href="examples/06_nurbs_trajectory.py"><b>NURBS trajectory</b></a></td>
  </tr>
  <tr align="center">
    <td>
      <img src=".github/04_camera_colored_point_cloud.gif" width="1024px"/>
    </td>
    <td>
      <img src=".github/05_smpl_movement.gif" width="1024px"/>
    </td>
    <td>
      <img src=".github/06_nurbs_trajectory.jpg" width="1024px"/>
    </td>
  </tr>
</table>

## Documentation

## Contributors

Blendify is written and maintained by [Vladimir Guzov](https://github.com/vguzov) and [Ilya Petrov](https://github.com/ptrvilya).

## Acknowledgment
We thank Verica Lazova for providing her Blender rendering scripts. Our code for processing point clouds is mostly based on the amazing [Blender-Photogrammetry-Importer](https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer) addon.

<!-- ## Citation -->

## License

The Python logo is trademark of Python Software Foundation.
The Blender logo is a registered property of Blender Foundation.
