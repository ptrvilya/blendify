from .lights import LightsCollection
from .renderables import RenderablesCollection
from .internal import Singleton
from .cameras import Camera


class Scene(metaclass=Singleton):
    renderables = RenderablesCollection()
    lights = LightsCollection()
    camera: Camera = None

    def __init__(cls):
        pass

    @classmethod
    def update_camera(cls, camera: Camera):
        cls.camera = camera
        cls.renderables.update_camera(camera)

    @classmethod
    def render(cls):
        pass

    @classmethod
    def export_scene(cls):
        pass
