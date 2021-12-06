from .lights import LightsCollection
from .renderables import RenderablesCollection
from .internal import Singleton


class Scene(metaclass=Singleton):
    renderables = RenderablesCollection()
    lights = LightsCollection()
    camera = None


    @classmethod
    def init(cls):
        pass

    @classmethod
    def set_camera(cls):
        pass
