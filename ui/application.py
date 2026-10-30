import traceback

import dearpygui.dearpygui as dpg


class Application:

    def initialize(self):

        dpg.create_context()

        dpg.configure_app(
            docking=True,
            docking_space=True,
            # Run widget callbacks on the main thread, between frames. By default
            # DearPyGui runs them on its own thread, racing with the render loop.
            manual_callback_management=True,
        )

        dpg.create_viewport(
            title="Spacecraft Configurator",
            width=1920,
            height=1080,
        )

        dpg.setup_dearpygui()
        dpg.show_viewport()

    def running(self):
        return dpg.is_dearpygui_running()

    @staticmethod
    def run_callbacks():
        """Run queued widget callbacks on this (the main) thread."""
        jobs = dpg.get_callback_queue()
        if not jobs:
            return
        for job in jobs:
            try:
                dpg.run_callbacks([job])
            except Exception:
                traceback.print_exc()  # a failing callback must not kill the app

    def render(self):
        self.run_callbacks()
        dpg.render_dearpygui_frame()

    def shutdown(self):
        dpg.destroy_context()