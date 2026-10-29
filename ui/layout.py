import dearpygui.dearpygui as dpg


def create_dockspace():

    #
    # Menu Bar
    #

    with dpg.viewport_menu_bar():

        with dpg.menu(
            label="File",
        ):

            dpg.add_menu_item(
                label="Exit",
            )

        with dpg.menu(
            label="Simulation",
        ):

            dpg.add_menu_item(
                label="Reset",
            )

        with dpg.menu(
            label="View",
        ):

            dpg.add_menu_item(
                label="Controls",
            )

            dpg.add_menu_item(
                label="Metrics",
            )

            dpg.add_menu_item(
                label="Console",
            )

    #
    # Root Host Window
    #

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

    #
    # Simulation Viewport
    #

    with dpg.window(
        label="Viewport",
        tag="simulation_window",
    ):

        dpg.add_text(
            "Renderer: OpenGL",
            tag="renderer_text",
        )

        dpg.add_separator()

        #
        # Dynamic viewport region.
        #
        # The renderer determines the actual size.
        #

        with dpg.child_window(
            tag="viewport_region",
            autosize_x=True,
            autosize_y=True,
            border=False,
        ):

            with dpg.texture_registry(
                tag="viewport_texture_registry",
            ):

                dpg.add_dynamic_texture(
                    width=1,
                    height=1,
                    default_value=[
                        0.0,
                        0.0,
                        0.0,
                        1.0,
                    ],
                    tag="viewport_texture",
                )

            dpg.add_image(
                "viewport_texture",
                tag="viewport_image",
            )

        dpg.add_separator()

        dpg.add_text(
            "Ready",
            tag="viewport_status",
        )

    #
    # Console
    #

    with dpg.window(
        label="Console",
        tag="console_window",
        width=1400,
        height=200,
    ):

        dpg.add_text(
            "Simulation Console",
        )

        dpg.add_separator()

        dpg.add_child_window(
            tag="console_output",
            autosize_x=True,
            autosize_y=True,
        )