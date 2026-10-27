import dearpygui.dearpygui as dpg
from registry import SIMULATIONS


class SimulationUI:

    def __init__(self, simulation_manager):
        self.manager = simulation_manager
        self.paused = False

        # --- STATE VARIABLES FOR ARROWS & CELESTIAL MILESTONES ---
        self.last_active_param = None
        self.last_active_widget_id = None
        self.slider_themes = {}

        self.CELESTIAL_MILESTONES = {
            "Moon 🌚": 1.62,
            "Mars 🔴": 3.71,
            "Earth 🌍": 9.81
        }

        dpg.create_context()

        # Set up global keyboard listener for left/right arrow navigation
        with dpg.handler_block():
            dpg.add_key_press_handler(
                dpg.mvKey_Left, callback=self._handle_arrow_navigation, user_data="down"
            )
            dpg.add_key_press_handler(
                dpg.mvKey_Right, callback=self._handle_arrow_navigation, user_data="up"
            )

        with dpg.window(
            label="Controls",
            width=400,
            height=700,
        ):
            dpg.add_text("Simulation Framework")
            dpg.add_separator()
            dpg.add_text("Simulation")

            dpg.add_combo(
                items=list(SIMULATIONS.keys()),
                default_value="Bouncing Balls",
                callback=self.change_simulation,
            )

            dpg.add_separator()

            dpg.add_button(
                label="Reset Simulation",
                callback=self.reset_simulation,
            )

            dpg.add_checkbox(
                label="Paused",
                default_value=False,
                callback=self.toggle_pause,
            )

            dpg.add_separator()
            dpg.add_text("Parameters")

            dpg.add_group(tag="parameter_container")

        dpg.create_viewport(
            title="Controls",
            width=400,
            height=700,
        )

        dpg.setup_dearpygui()
        dpg.show_viewport()

        self.rebuild_parameter_ui()

    def toggle_pause(self, sender, app_data, user_data):
        self.paused = app_data

    def change_simulation(self, sender, app_data, user_data):
        self.manager.load(app_data)
        self.rebuild_parameter_ui()

    def reset_simulation(self, sender, app_data, user_data):
        self.manager.reset()

    def update_parameter(self, sender, app_data, parameter):
        parameter.value = app_data

    # --- UPGRADED PARAMETER GENERATOR LOOP ---
    def rebuild_parameter_ui(self):
        dpg.delete_item("parameter_container", children_only=True)

        simulation = self.manager.current
        if simulation is None:
            return

        for parameter in simulation.parameters.values():
            widget_tag = f"slider_{parameter.name}"
            theme_tag = f"theme_{parameter.name}"
            self.slider_themes[parameter.name] = theme_tag

            # Register a dynamic canvas style theme for the widgets
            with dpg.theme(tag=theme_tag):
                with dpg.theme_component(dpg.mvAll):
                    pass

            # Detect configuration types (handling floats vs ints/bools if your engine uses them)
            if isinstance(parameter.value, float):
                # Match Earth's gravity cleanly by ensuring the max range extends up to 12.0
                max_val = 12.0 if parameter.name.lower() == "gravity" else getattr(parameter, "max", 1.0)

                dpg.add_slider_float(
                    tag=widget_tag,
                    label=parameter.name,
                    default_value=parameter.value,
                    min_value=getattr(parameter, "min", 0.0),
                    max_value=max_val,
                    callback=self._on_slider_interact,
                    user_data=(parameter, widget_tag),
                    parent="parameter_container",
                )
                dpg.bind_item_theme(widget_tag, theme_tag)

                # Inject the interactive planet milestone readout directly under gravity
                if parameter.name.lower() == "gravity":
                    dpg.add_text(
                        "Milestone: Custom Environment",
                        tag="gravity_milestone_text",
                        color=[150, 150, 150, 255],
                        parent="parameter_container"
                    )
                    self._update_gravity_theme(parameter.value, parameter)
            else:
                # Fallback slider for discrete values or ints
                dpg.add_slider_float(
                    tag=widget_tag,
                    label=parameter.name,
                    default_value=float(parameter.value),
                    min_value=float(getattr(parameter, "min", 0)),
                    max_value=float(getattr(parameter, "max", 100)),
                    callback=self._on_slider_interact,
                    user_data=(parameter, widget_tag),
                    parent="parameter_container",
                )

    # --- ACTION CAPTURE AND RENDERING CONTROL METHODS ---
    def _on_slider_interact(self, sender, app_data, user_data):
        """Remembers what you clicked and targets it for arrow key navigation."""
        parameter, widget_tag = user_data
        self.last_active_param = parameter
        self.last_active_widget_id = widget_tag

        if parameter.name.lower() == "gravity":
            self._update_gravity_theme(app_data, parameter)

        self.update_parameter(sender, app_data, parameter)

    def _update_gravity_theme(self, current_gravity, parameter):
        """Calculates color shifting paths and updates celestial text alignments."""
        min_g = getattr(parameter, "min", 0.0)
        max_g = 12.0

        # Calculate a color scalar percentage
        span = (max_g - min_g) if (max_g - min_g) != 0 else 1.0
        pct = (current_gravity - min_g) / span
        
        # Color shifting values: cool grey sliding smoothly into a warning dark crimson
        r = int(70 + (pct * 110))
        g = int(80 - (pct * 65))
        b = int(95 - (pct * 80))

        theme_tag = self.slider_themes.get(parameter.name)
        if theme_tag and dpg.does_item_exist(theme_tag):
            dpg.delete_item(theme_tag, children_only=True)
            with dpg.theme_component(dpg.mvAll, parent=theme_tag):
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, [r, g, b, 255])
                dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, [min(255, r + 30), g, b, 255])

        # Evaluate target thresholds
        matched_milestone = "Custom Environment"
        text_color = [150, 150, 150, 255]
        tolerance = 0.15

        for name, value in self.CELESTIAL_MILESTONES.items():
            if abs(current_gravity - value) <= tolerance:
                matched_milestone = f"Matched: {name} Gravity ({value} m/s²)"
                if "Earth" in name:
                    text_color = [80, 165, 245, 255]
                elif "Mars" in name:
                    text_color = [240, 100, 80, 255]
                elif "Moon" in name:
                    text_color = [245, 230, 135, 255]
                break

        if dpg.does_item_exist("gravity_milestone_text"):
            dpg.set_value("gravity_milestone_text", f"Milestone: {matched_milestone}")
            dpg.configure_item("gravity_milestone_text", color=text_color)

    def _handle_arrow_navigation(self, sender, app_data, direction):
        """Intercepts Left/Right arrow keys to maneuver the last interacted slider."""
        if not self.last_active_param or dpg.is_item_active(self.last_active_widget_id):
            return

        current_val = dpg.get_value(self.last_active_widget_id)
        step = 0.01
        
        new_val = current_val + step if direction == "up" else current_val - step
        max_val = 12.0 if self.last_active_param.name.lower() == "gravity" else getattr(self.last_active_param, "max", 1.0)
        new_val = max(getattr(self.last_active_param, "min", 0.0), min(max_val, new_val))

        dpg.set_value(self.last_active_widget_id, new_val)

        if self.last_active_param.name.lower() == "gravity":
            self._update_gravity_theme(new_val, self.last_active_param)

        self.update_parameter(self.last_active_widget_id, new_val, self.last_active_param)

    def render(self):
        dpg.render_dearpygui_frame()

    def shutdown(self):
        dpg.destroy_context()
