"""
MIT License

Copyright (c) 2018 Sebastian Bullinger
Copyright (c) 2021 Vladimir Guzov and Ilya Petrov

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import bpy


def compute_particle_color_texture(colors, name="ParticleColor"):
    # To view the texture we set the height of the texture to vis_image_height
    image = bpy.data.images.new(name=name, width=len(colors), height=1)

    _copy_values_to_image(colors, image.name)
    image = bpy.data.images[image.name]
    # https://docs.blender.org/api/current/bpy.types.Image.html#bpy.types.Image.pack
    image.pack()
    return image


def _copy_values_to_image(value_tuples, image_name):
    """ Copy values to image pixels
    """
    image = bpy.data.images[image_name]
    # working on a copy of the pixels results in a MASSIVE performance speed
    local_pixels = list(image.pixels[:])
    for value_index, value_tuple in enumerate(value_tuples):
        column_offset = value_index * 4  # (R,G,B,A)
        # Order is R,G,B, opacity
        local_pixels[column_offset] = value_tuple[0]
        local_pixels[column_offset + 1] = value_tuple[1]
        local_pixels[column_offset + 2] = value_tuple[2]

        # opacity (0 = transparent, 1 = opaque)
        if len(value_tuple) == 4:
            local_pixels[column_offset + 3] = value_tuple[3]
        else:
            # local_pixels[column_offset + 3] = 1.0    # already set by default
            pass

    image.pixels = local_pixels[:]
