from typing import Union

import bpy

from ..renderables.base import Renderable


def set_shadow_catcher(obj: Union[str, Renderable], state=False):
    """Set object is_shadow_catcher and various visibility_* properties to make
    object act as a shadow catcher or revert the changes.

    Args:
        obj (Union[str, Renderable]): tag of the Blender object or instance of Renderable
        state (bool): if True make obj a shadow catcher, otherwise make it a regular object
    """
    if not isinstance(obj, str):
        obj = obj.tag

    # select object
    bpy.data.objects[obj].select_set(True)
    bpy.context.view_layer.objects.active = bpy.data.objects[obj]
    shadow_catcher = bpy.context.active_object

    # set / unset shadow catcher properties
    shadow_catcher.is_shadow_catcher = state
    shadow_catcher.cycles.is_shadow_catcher = state
    shadow_catcher.visible_glossy = not state
    shadow_catcher.visible_diffuse = not state
    shadow_catcher.visible_transmission = not state
    shadow_catcher.visible_volume_scatter = not state

    # deselect object
    bpy.data.objects[obj].select_set(False)
