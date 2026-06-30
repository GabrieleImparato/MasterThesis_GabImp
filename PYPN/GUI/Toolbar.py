import tkinter as tk

from Controller.SimulationEngine import SimulationEngine


class Toolbar(tk.Frame):
    def __init__(self, parent, canvas, **kwargs):
        super().__init__(parent, bd=1, relief=tk.RAISED, **kwargs)
        self.canvas = canvas
        self.active_button = None
        self.mode_var = tk.StringVar(value="Select")
        self.simulation_engine = None
        self.create_buttons()

    def create_buttons(self):
        tk.Label(self, text="Tools", font=("Arial", 10, "bold")).pack(anchor="w", padx=6, pady=(6, 4))
        tk.Label(self, textvariable=self.mode_var, fg="#2563eb", anchor="w").pack(anchor="w", padx=6, pady=(0, 6))

        sections = [
            ("Edit", [("Select", "select"), ("Add place", "place"), ("Add transition", "transition"), ("Add arc", "arc")]),
            ("Run", [("Fire transition", "fire"), ("Auto simulate", "auto"), ("Stop auto", "stop_auto"), ("Delete selected", "delete"), ("Reset", "reset")]),
        ]

        for title, buttons in sections:
            tk.Label(self, text=title, font=("Arial", 9, "bold"), fg="#555").pack(anchor="w", padx=6, pady=(4, 2))
            for text, mode in buttons:
                btn = tk.Button(self, text=text, command=lambda m=mode: self.handle_action(m), width=14)
                btn.pack(padx=6, pady=2, fill=tk.X)
                if mode == "select":
                    self.active_button = btn

        tk.Label(self, text="Tip: double-click a node to edit it", fg="#666", justify="left", wraplength=150).pack(anchor="w", padx=6, pady=(8, 6))

    def handle_action(self, mode):
        if mode == "fire":
            self.fire_transition()
            return
        if mode == "auto":
            self.start_auto_simulation()
            return
        if mode == "stop_auto":
            self.stop_auto_simulation()
            return
        if mode == "delete":
            self.delete_selected()
            return
        if mode == "reset":
            self.reset_canvas()
            return
        if self.canvas is not None:
            self.canvas.set_mode(mode)
            self.update_mode(mode)

    def update_mode(self, mode):
        mode_label = {
            "select": "Select",
            "place": "Add place",
            "transition": "Add transition",
            "arc": "Add arc",
        }.get(mode, mode.capitalize())
        self.mode_var.set(f"Mode: {mode_label}")
        if self.active_button is not None:
            self.active_button.config(relief=tk.RAISED)

    def start_auto_simulation(self):
        if self.simulation_engine is None:
            self.simulation_engine = SimulationEngine(self.canvas, interval_ms=1000)
        self.simulation_engine.start()
        self.canvas.inspector.show_message("Auto simulation started")

    def stop_auto_simulation(self):
        if self.simulation_engine is not None:
            self.simulation_engine.stop()
        self.canvas.inspector.show_message("Auto simulation stopped")

    def fire_transition(self):
        node = self.canvas.selected_node
        if node is None or node.node_type != "transition":
            self.canvas.inspector.show_message("Select a transition to fire")
            return
        try:
            if self.canvas.net.is_enabled(node.obj):
                self.canvas.net.fire(node.obj)
                self.canvas.inspector.show_message(f"Fired {node.obj.name}")
            else:
                self.canvas.inspector.show_message(f"Transition {node.obj.name} is not enabled")
        except Exception as exc:
            self.canvas.inspector.show_message(str(exc))

    def delete_selected(self):
        self.canvas.delete_selected_node()

    def reset_canvas(self):
        self.canvas.delete("all")
        self.canvas.nodes.clear()
        self.canvas.arcs.clear()
        self.canvas.pending_arc_source = None
        self.canvas.selected_node = None
        self.canvas.net.places.clear()
        self.canvas.net.transitions.clear()
        self.canvas.net.arcs.clear()
        self.canvas.inspector.show_message("Canvas reset")
