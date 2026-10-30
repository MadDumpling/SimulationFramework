from abc import ABC, abstractmethod


class Renderer(ABC):
    """Offscreen 3D renderer that presents into the DearPyGui viewport texture."""

    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def running(self):
        pass

    @property
    @abstractmethod
    def aspect(self):
        pass

    @abstractmethod
    def begin_frame(self):
        pass

    @abstractmethod
    def set_camera(self, view_projection, eye):
        pass

    @abstractmethod
    def draw_mesh(
        self,
        key,
        mesh,
        model,
        color,
        highlight=0.0,
        pick_id=0,
    ):
        pass

    @abstractmethod
    def draw_lines_3d(self, points, color):
        pass

    @abstractmethod
    def pick(self, x, y):
        pass

    @abstractmethod
    def end_frame(self):
        pass
