import dearpygui.dearpygui as dpg


def create_dockspace():

    with dpg.viewport_menu_bar():

        with dpg.menu(
            label="File",
        ):

            dpg.add_menu_item(
                label="Exit",
            )

    with dpg.window(
        tag="Primary Window",
        no_background=True,
        no_title_bar=True,
        no_move=True,
        no_resize=True,
        no_close=True,
        no_collapse=True,
    ):
        pass

    with dpg.window(
        label="Simulation",
        tag="simulation_window",
    ):

        with dpg.texture_registry():

            dpg.add_dynamic_texture(
                width=1280,
                height=720,
                default_value=[
                    0.0
                ] * (
                    1280
                    * 720
                    * 4
                ),
                tag="viewport_texture",
            )

        dpg.add_image(
            "viewport_texture"
        )

    with dpg.window(
        label="Console",
        tag="console_window",
    ):

        dpg.add_text(
            "Console",
        )