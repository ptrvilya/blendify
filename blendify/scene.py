from .lights import LightsCollection
from .renderables import RenderablesCollection
from .internal import Singleton
from .cameras import Camera


class Scene(metaclass=Singleton):
    def __init__(self, camera: Camera):
        self.renderables = RenderablesCollection(camera)
        self.lights = LightsCollection()
        self.camera: Camera = camera

    def update_camera(self, camera: Camera):
        self.camera = camera
        self.renderables.update_camera(camera)

    def render(self):
        pass

    def export_scene(self):
        pass

    def attach_blend(self):
        pass
