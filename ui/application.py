import dearpygui.dearpygui as dpg


class Application:

    def initialize(self):

        dpg.create_context()

        dpg.configure_app(
            docking=True,
            docking_space=True,
        )

        dpg.create_viewport(
            title="Simulation Sandbox",
            width=1920,
            height=1080,
        )

        dpg.setup_dearpygui()
        dpg.show_viewport()

    def running(self):
        return dpg.is_dearpygui_running()

    def render(self):
        dpg.render_dearpygui_frame()

    def shutdown(self):
        dpg.destroy_context()