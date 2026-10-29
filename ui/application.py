import dearpygui.dearpygui as dpg


class Application:

    WINDOW_WIDTH = 1920
    WINDOW_HEIGHT = 1080

    def initialize(self):

        dpg.create_context()

        dpg.configure_app(
            docking=True,
            docking_space=True,
        )

        dpg.create_viewport(
            title="Simulation Sandbox",
            width=self.WINDOW_WIDTH,
            height=self.WINDOW_HEIGHT,
            resizable=True,
        )

        dpg.setup_dearpygui()

        dpg.show_viewport()

        dpg.maximize_viewport()

    def running(self):
        return dpg.is_dearpygui_running()

    def render(self):
        dpg.render_dearpygui_frame()

    def shutdown(self):
        dpg.destroy_context()