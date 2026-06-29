import tkinter as tk

class Toolbar(tk.Frame):
    def __init__(self, parent, canvas, **kwargs):
        super().__init__(parent, bd=1, relief=tk.RAISED, **kwargs)
        self.canvas = canvas
        self.create_buttons()

    def create_buttons(self):
        tk.Button(self, text="Select", command=lambda: self.canvas.set_mode("select"), width=12).pack(padx=4, pady=4)
        tk.Button(self, text="Add place", command=lambda: self.canvas.set_mode("place"), width=12).pack(padx=4, pady=4)
        tk.Button(self, text="Add transition", command=lambda: self.canvas.set_mode("transition"), width=12).pack(padx=4, pady=4)
        tk.Button(self, text="Add arc", command=lambda: self.canvas.set_mode("arc"), width=12).pack(padx=4, pady=4)
        tk.Button(self, text="Fire transition", command=self.fire_transition, width=12).pack(padx=4, pady=4)
        tk.Button(self, text="Delete selected", command=self.delete_selected, width=12).pack(padx=4, pady=4)
        tk.Button(self, text="Reset", command=self.reset_canvas, width=12).pack(padx=4, pady=4)

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
