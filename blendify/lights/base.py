from abc import ABC, abstractmethod


class Light(ABC):
    @abstractmethod
    def __init__(self, tag: str):
        super().__init__()
        self._tag = tag
