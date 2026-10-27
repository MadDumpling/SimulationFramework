import dearpygui.dearpygui as dpg


def create_dockspace():

    with dpg.viewport_menu_bar():

        with dpg.menu(label="File"):
            dpg.add_menu_item(
                label="Exit"
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
        dpg.add_text(
            "Simulation Viewport"
        )

    with dpg.window(
        label="Console",
        tag="console_window",
    ):
        dpg.add_text(
            "Console"
        )