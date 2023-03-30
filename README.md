<!-- ![blendify Logo](.github/blendify_logo_dark_bg.png#gh-dark-mode-only) -->
<!-- ![blendify Logo](.github/blendify_logo_light_bg.png#gh-light-mode-only) -->
![blendify Logo](.github/blendify_logo_light_bg.png)

## Introduction
Blendify is a framework providing high-level API to create and render scenes with Blender directly from Python.
Blendify is designed to provide simplified access to selected blender structures and makes it possible to work with 
them from any python script.

Key-features:
* Quick and easy start: no need to dive into Blender API
* Focus on common mesh and point cloud visualization tasks
* Simple and unified interface to populate scene with objects, lights amd camera
* Support for textured meshes and colored point clouds 


## Installation instructions
Installing blendify from git: `pip install git+https://gitlab.com/real-virtual-humans/visuals/blendify.git`


## Quick Start
```python
# Script to render cube
import blendify as bfy
# Get scene
scene = bfy.get_scene()
# Add light
scene.lights.add_point(strength=1000, translation=(4, -2, 4))
# Add camera
scene.set_perspective_camera((512, 512), fov_x=0.7, quaternion=(0.82, 0.42, 0.18, 0.34), translation=(5, -5, 5))
# Create material
material = bfy.materials.PrinsipledBSDFMaterial()
# Create color
color = bfy.colors.UniformColors((0.0, 1.0, 0.0))
# Add cube mesh
scene.renderables.add_cube_mesh(1.0, material, color)
# Render scene
scene.render(filepath="cube.jpg")
```


## Examples
Examples are described in [examples.md](docs/examples.md).
<table>
  <tr align="center">
    <td><a href="examples/01_cornell_box.py"><b>Cornell Box</b></a></td>
    <td><a href="examples/02_color_albedo_depth.py"><b>Color, albedo and depth</b></a></td>
    <td><a href="examples/03_mesh_with_texture.py"><b>Mesh with texture</b></a></td>
  </tr>
  <tr align="center">
    <td>
      <img src=".github/01_cornell_box.jpg" width="310px"/>
    </td>
    <td>
      <img src=".github/02_color_albedo_depth.jpg" width="310px"/>
    </td>
    <td>
      <img src=".github/03_mesh_with_texture.jpg" width="310px"/>
    </td>
  </tr>
  <tr align="center">
    <td><a href="examples/04_camera_colored_point_cloud.py"><b>Camera colored point cloud</b></a></td>
    <td><a href="examples/05_smpl_movement.py"><b>SMPL movement</b></a></td>
    <td><a href="examples/06_nurbs_trajectory.py"><b>NURBS trajectory</b></a></td>
  </tr>
  <tr align="center">
    <td>
      <img src=".github/04_camera_colored_point_cloud.gif" width="310px"/>
    </td>
    <td>
      <img src=".github/05_smpl_movement.gif" width="310px"/>
    </td>
    <td>
      <img src=".github/06_nurbs_trajectory.gif" width="310px"/>
    </td>
  </tr>
</table>


## Works that use blendify
* [B.L. Bhatnagar, X. Xie, **I. Petrov**, C. Sminchisescu, C. Theobalt, G. Pons-Moll: 
  BEHAVE: Dataset and Method for Tracking Human Object Interactions, in CVPR'22](https://virtualhumans.mpi-inf.mpg.de/behave/)
* [V. Lazova, E. Insafutdinov, G. Pons-Moll: 360-Degree Textures of People in Clothing from a Single Image
in 3DV'19.](https://virtualhumans.mpi-inf.mpg.de/360tex/)
* [X. Zhang, B.L. Bhatnagar, **V. Guzov**, S. Starke, G. Pons-Moll: 
  COUCH: Towards Controllable Human-Chair Interactions](https://virtualhumans.mpi-inf.mpg.de/couch/)
* [G. Tiwari, D. Antic, J. E. Lenssen, N. Sarafianos, T. Tung, G. Pons-Moll: Pose-NDF: 
Modeling Human Pose Manifolds with Neural Distance Fields](https://virtualhumans.mpi-inf.mpg.de/posendf/)
* [**I. Petrov**, R. Marin, J. Chibane, G. Pons-Moll: Object pop-up: Can we infer 3D objects and their poses from human interactions alone?](https://virtualhumans.mpi-inf.mpg.de/object_popup/)

## Contributors
Blendify is written and maintained by [Vladimir Guzov](https://github.com/vguzov) and [Ilya Petrov](https://github.com/ptrvilya).


## Acknowledgment
We thank Verica Lazova for providing her Blender rendering scripts. 
Our code for processing point clouds is mostly based on the amazing [Blender-Photogrammetry-Importer][BPI] addon.


## License
The code is released under the [GNU General Public License v3][GNU GPL v3].

The Python logo is trademark of Python Software Foundation.
The Blender logo is a registered property of Blender Foundation.
[Blender-Photogrammetry-Importer][BPI] is distributed under the [MIT License][BPI license]. 
Blender is released under the [GNU General Public License v3][GNU GPL v3]. 

[GNU GPL v3]: https://www.gnu.org/licenses/gpl-3.0.html
[BPI]: https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer
[BPI license]: https://github.com/SBCV/Blender-Addon-Photogrammetry-Importer/blob/master/README.md
