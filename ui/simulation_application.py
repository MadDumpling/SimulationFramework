"""Primary application shell for the spacecraft configuration workbench."""

from core import EventBus

from .spacecraft_designer import SpacecraftDesignerUI


class SimulationApplication:
    """Preserve the entry-point API while making spacecraft design primary."""

    def __init__(self):
        self.events = EventBus()
        self.spacecraft_ui = SpacecraftDesignerUI(self.events)
        self._initialized = False

    @property
    def running(self):
        # DearPyGui owns the application lifetime in Application.running().
        return True

    def initialize(self):
        if self._initialized:
            return
        self.spacecraft_ui.build()
        self._initialized = True

    def update(self):
        # The designer is event-driven; mission propagation runs on demand.
        pass

    def render(self):
        # DearPyGui presents the designer through Application.render().
        pass