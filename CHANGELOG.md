# blendify 2.1.0
We are excited to bring the support to the latest Blender LTS version to blendify.

- Updated the code to rely on `Blender 4.5.2 LTS` and `Python 3.11`;
- Switched build logic to use `pyproject.toml` instead of `setup.py`;
- Internal: added force exit logic using `atexit` to circumvent Blender's bug with hanging process during memory cleanup on exit;

### Breaking changes
several changes were required to match the updated Blender API:
- Lights: renamed `cast_shadows` to `use_shadow`;
- Materials: renamed material properties to match the updated Blender API (Clear Coat -> Coat IOR, Specular -> Specualr IOR Level, etc.).


# blendify 2.0.1
This update is a minor release that incorporates a UV map leakage fix ([pull request #11](https://github.com/ptrvilya/blendify/pull/11)) and moves the example 05 assets location.

# blendify 2.0.0
We are excited to announce the second major release of blendify.

This release, among other minor improvements, introduces a more flexible way of defining the material, more material presets, support for different rotation representations, improved light parsing, and fast rendering with the `eevee` engine to preview the result.

Some of the changes are not backward compatible with the previous version of blendify; the breaking changes are listed below:

### Breaking changes
- Removed `attach_blend_w_camera` from `Scene`;
now parsing is controlled via `with_camera` parameter in `Scene.attach_blend()`
- Removed `PrinsipledMaterial`, a mistyped name for `PrincipledBSDFMaterial`;
- Renamed the `quaternion` parameter in `Positionable` to `rotation`;
rotation mode is now controlled via the `rotation_mode` parameter;
- To compress the repository, we have cleaned the history of modifications for big files (mostly `gif`), resulting in a new commit tree;
- Flipped texture reading row order in `TextureColors` to be compatible with `FileTextureColors`.

## Summary of other changes and improvements:

### Materials
- Implemented a flexible way to define new materials using shading nodes from Blender;
This allowed us to implement a combination of materials, e.g., `PrincipledBSDF` with `Wireframe` on top;
- Added several presets for `PrincipledBSDFMaterial` to ease material creation (`PlasticMaterial`, `MetalMaterial`, and similar materials with wireframe on top);

### Lights
- Implemented parsing of light sources to `LightsCollection` from `.blend` file (via `Scene.attach_blend()`);
- Added `set_background_light` method to `LightsCollection` to set ambient lighting via world shading nodes in Blender;

### Object manipulation
- Extended support for different rotation representations in `Positionable` objects;
Now all common representations (quaternion, Euler angles, axis-angle, rotation matrix) are supported;
- Implemented `look_at` as a rotation mode for `Positionable` objects to ease camera positioning;

### Other
- Unified `.blend` parsing logic for parsing with and without a camera;
- Implemented fast preview via `eevee` engine to allow for intermediate previews of the scene;
- Added plane primitive to ease implementing shadow catchers (code is provided in `Example 7`);
- Added pointcloud to textured mesh conversion function in `blendify.utils`;
- Updated the code to rely on `Blender 3.6.0 LTS`.