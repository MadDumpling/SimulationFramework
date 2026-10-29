import dearpygui.dearpygui as dpg


class ViewportManager:

    def __init__(
        self,
        renderer,
    ):

        self.renderer = renderer

        self.width = 0
        self.height = 0

    def update(self):

        if not dpg.does_item_exist(
            "viewport_region"
        ):
            return

        width = int(
            dpg.get_item_width(
                "viewport_region"
            )
        )

        height = int(
            dpg.get_item_height(
                "viewport_region"
            )
        )

        if width < 32:
            return

        if height < 32:
            return

        if (
            width == self.width
            and height == self.height
        ):
            return

        self.resize(
            width,
            height,
        )

    def resize(
        self,
        width,
        height,
    ):

        self.width = width
        self.height = height

        print(
            f"Viewport resized "
            f"{width}x{height}"
        )

        self.renderer.resize(
            width,
            height,
        )

        #self._recreate_texture()

    def _recreate_texture(self):

        texture_size = (
            self.width
            * self.height
            * 4
        )

        if dpg.does_item_exist(
            "viewport_texture"
        ):
            dpg.delete_item(
                "viewport_texture"
            )

        with dpg.texture_registry(
            show=False,
            tag="viewport_texture_registry",
        ):

            dpg.add_dynamic_texture(
                width=self.width,
                height=self.height,
                default_value=[
                    0.0
                ] * texture_size,
                tag="viewport_texture",
            )

        if dpg.does_item_exist(
            "viewport_image"
        ):
            dpg.delete_item(
                "viewport_image"
            )

        dpg.add_image(
            "viewport_texture",
            parent="viewport_region",
            tag="viewport_image",
        )

        dpg.configure_item(
            "viewport_image",
            width=self.width,
            height=self.height,
        )