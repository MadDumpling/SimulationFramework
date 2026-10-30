import dearpygui.dearpygui as dpg


def create_dockspace():

    with dpg.viewport_menu_bar():

        with dpg.menu(
            label="File",
        ):

            dpg.add_menu_item(
                label="Exit",
                callback=dpg.stop_dearpygui,
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
        label="Viewport",
        tag="viewport_window",
        width=1300,
        height=800,
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

        dpg.add_text(
            "Left-drag orbit · Right/middle-drag pan · Wheel zoom · "
            "Click select · F frame · R reset",
            color=(150, 165, 185),
        )

        dpg.add_image(
            "viewport_texture",
            tag="viewport_image",
        )

        dpg.add_text(
            "",
            tag="fps_text",
            color=(150, 165, 185),
        )
