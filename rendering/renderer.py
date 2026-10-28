from abc import ABC, abstractmethod


class Renderer(ABC):

    @property
    @abstractmethod
    def running(self):
        pass

    @abstractmethod
    def begin_frame(self):
        pass

    @abstractmethod
    def draw_circles(
        self,
        positions,
        radius,
        color,
    ):
        pass

    @abstractmethod
    def end_frame(self):
        pass
