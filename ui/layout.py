import dearpygui.dearpygui as dpg


def _apply_space_theme():
    with dpg.theme() as theme, dpg.theme_component(dpg.mvAll):
        for color, value in (
            (dpg.mvThemeCol_WindowBg, (13, 19, 31, 255)),
            (dpg.mvThemeCol_ChildBg, (17, 26, 42, 255)),
            (dpg.mvThemeCol_PopupBg, (20, 30, 48, 255)),
            (dpg.mvThemeCol_Text, (225, 233, 244, 255)),
            (dpg.mvThemeCol_Border, (50, 67, 91, 255)),
            (dpg.mvThemeCol_FrameBg, (26, 39, 59, 255)),
            (dpg.mvThemeCol_FrameBgHovered, (38, 58, 84, 255)),
            (dpg.mvThemeCol_FrameBgActive, (48, 72, 101, 255)),
            (dpg.mvThemeCol_TitleBg, (13, 19, 31, 255)),
            (dpg.mvThemeCol_TitleBgActive, (22, 34, 54, 255)),
            (dpg.mvThemeCol_Button, (31, 55, 81, 255)),
            (dpg.mvThemeCol_ButtonHovered, (43, 82, 116, 255)),
            (dpg.mvThemeCol_ButtonActive, (50, 104, 141, 255)),
            (dpg.mvThemeCol_Header, (24, 48, 72, 255)),
            (dpg.mvThemeCol_HeaderHovered, (34, 69, 100, 255)),
            (dpg.mvThemeCol_HeaderActive, (42, 87, 120, 255)),
            (dpg.mvThemeCol_Tab, (21, 34, 53, 255)),
            (dpg.mvThemeCol_TabHovered, (40, 76, 107, 255)),
            (dpg.mvThemeCol_TabActive, (32, 63, 91, 255)),
            (dpg.mvThemeCol_CheckMark, (255, 170, 64, 255)),
            (dpg.mvThemeCol_SliderGrab, (255, 170, 64, 255)),
            (dpg.mvThemeCol_SliderGrabActive, (255, 195, 105, 255)),
        ):
            dpg.add_theme_color(color, value)
        for style, value in (
            (dpg.mvStyleVar_WindowRounding, 8),
            (dpg.mvStyleVar_FrameRounding, 5),
            (dpg.mvStyleVar_GrabRounding, 5),
            (dpg.mvStyleVar_TabRounding, 5),
            (dpg.mvStyleVar_WindowPadding, (12, 12)),
            (dpg.mvStyleVar_FramePadding, (8, 5)),
            (dpg.mvStyleVar_ItemSpacing, (8, 7)),
        ):
            if isinstance(value, tuple):
                dpg.add_theme_style(style, *value)
            else:
                dpg.add_theme_style(style, value)
    dpg.bind_theme(theme)


def create_dockspace():
    _apply_space_theme()
    with dpg.viewport_menu_bar(), dpg.menu(label="File"):
        dpg.add_menu_item(
            label="Exit",
            callback=dpg.stop_dearpygui,
        )

    with dpg.window(
        tag="primary_window",
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
        pos=(525, 28),
        width=1385,
        height=1025,
    ):
        with dpg.texture_registry():
            dpg.add_dynamic_texture(
                width=1280,
                height=720,
                default_value=[0.0] * (1280 * 720 * 4),
                tag="viewport_texture",
            )

        dpg.add_text(
            "Left-drag orbit · Right/middle-drag pan · Wheel zoom · "
            "Click select · F frame · R reset",
            color=(150, 165, 185),
        )
        dpg.add_text(" ", tag="mission_banner", wrap=1320)
        dpg.add_image(
            "viewport_texture",
            tag="viewport_image",
            width=1280,
            height=720,
        )
        dpg.add_text(
            "",
            tag="fps_text",
            color=(150, 165, 185),
        )
