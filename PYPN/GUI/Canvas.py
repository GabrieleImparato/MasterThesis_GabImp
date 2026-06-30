import tkinter as tk
from tkinter import messagebox


class NodeEditDialog(tk.Toplevel):
    def __init__(self, parent, canvas, node):
        super().__init__(parent)
        self.title(f"Edit {node.node_type}")
        self.transient(parent)
        self.resizable(False, False)
        self.canvas = canvas
        self.node = node

        tk.Label(self, text="Name:").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))
        self.name_var = tk.StringVar(value=node.obj.name)
        self.name_entry = tk.Entry(self, textvariable=self.name_var, width=30)
        self.name_entry.grid(row=0, column=1, padx=8, pady=(8, 4))

        tk.Label(self, text="X:").grid(row=1, column=0, sticky="w", padx=8, pady=(4, 4))
        self.x_var = tk.StringVar(value=str(int(node.x)))
        self.x_entry = tk.Entry(self, textvariable=self.x_var, width=10)
        self.x_entry.grid(row=1, column=1, sticky="w", padx=8, pady=(4, 4))

        tk.Label(self, text="Y:").grid(row=2, column=0, sticky="w", padx=8, pady=(4, 4))
        self.y_var = tk.StringVar(value=str(int(node.y)))
        self.y_entry = tk.Entry(self, textvariable=self.y_var, width=10)
        self.y_entry.grid(row=2, column=1, sticky="w", padx=8, pady=(4, 4))

        tk.Label(self, text="Allowed colors (comma-separated):").grid(row=3, column=0, sticky="w", padx=8, pady=(4, 4))
        colors = ", ".join(getattr(c, "name", c) for c in sorted(node.obj.colors, key=lambda x: getattr(x, "name", x)))
        self.colors_var = tk.StringVar(value=colors)
        self.colors_entry = tk.Entry(self, textvariable=self.colors_var, width=30)
        self.colors_entry.grid(row=3, column=1, padx=8, pady=(4, 4))

        if node.node_type == "place":
            tk.Label(self, text="Add token (color,count):").grid(row=4, column=0, sticky="w", padx=8, pady=(8, 4))
            self.token_color_var = tk.StringVar(value="")
            self.token_count_var = tk.StringVar(value="1")
            tk.Entry(self, textvariable=self.token_color_var, width=16).grid(row=4, column=1, sticky="w", padx=8, pady=(8, 4))
            tk.Entry(self, textvariable=self.token_count_var, width=8).grid(row=4, column=2, sticky="w", padx=(0, 8), pady=(8, 4))

            tk.Label(self, text="Remove token (color,count):").grid(row=5, column=0, sticky="w", padx=8, pady=(4, 4))
            self.remove_token_color_var = tk.StringVar(value="")
            self.remove_token_count_var = tk.StringVar(value="1")
            tk.Entry(self, textvariable=self.remove_token_color_var, width=16).grid(row=5, column=1, sticky="w", padx=8, pady=(4, 4))
            tk.Entry(self, textvariable=self.remove_token_count_var, width=8).grid(row=5, column=2, sticky="w", padx=(0, 8), pady=(4, 4))

        button_frame = tk.Frame(self)
        button_frame.grid(row=6, column=0, columnspan=3, pady=(8, 8))
        tk.Button(button_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="Delete", command=self.delete_node).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=4)

        self.name_entry.focus_set()
        self.bind("<Return>", lambda event: self.save())
        self.bind("<Escape>", lambda event: self.destroy())

    def _resolve_color(self, color_name):
        existing_color = next((color for color in self.canvas.net.colors if color.name == color_name), None)
        if existing_color is None:
            existing_color = self.canvas.net.add_color(color_name)
        return existing_color

    def delete_node(self):
        self.canvas.delete_node(self.node)
        self.destroy()

    def save(self):
        new_name = self.name_var.get().strip()
        if not new_name:
            messagebox.showerror("Invalid name", "The name cannot be empty")
            return

        try:
            new_x = int(self.x_var.get())
            new_y = int(self.y_var.get())
        except ValueError:
            messagebox.showerror("Invalid position", "Position values must be integers")
            return

        for other in self.canvas.nodes:
            if other is self.node:
                continue
            if other.node_type == self.node.node_type and other.obj.name == new_name:
                messagebox.showerror("Invalid name", f"A {self.node.node_type} with this name already exists")
                return

        new_x, new_y = self.canvas.snap_point(new_x, new_y)
        if not self.canvas.can_place_node(new_x, new_y, self.node):
            messagebox.showerror("Overlap not allowed", "Places and transitions cannot overlap")
            return

        self.node.obj.name = new_name
        self.canvas.itemconfigure(self.node.label_id, text=new_name)
        self.canvas.move_node(self.node, new_x, new_y)

        color_names = [name.strip() for name in self.colors_var.get().split(",") if name.strip()]
        resolved_colors = []
        for color_name in color_names:
            resolved_colors.append(self._resolve_color(color_name))
        self.node.obj.colors = set(resolved_colors)

        if self.node.node_type == "place":
            token_color_name = self.token_color_var.get().strip() if hasattr(self, "token_color_var") else ""
            token_count_text = self.token_count_var.get().strip() if hasattr(self, "token_count_var") else ""
            if token_color_name:
                try:
                    token_count = int(token_count_text) if token_count_text else 1
                except ValueError:
                    messagebox.showerror("Invalid token count", "Token count must be an integer")
                    return
                if token_count <= 0:
                    messagebox.showerror("Invalid token count", "Token count must be greater than zero")
                    return
                color = self._resolve_color(token_color_name)
                self.node.obj.add_allowed_color(color)
                self.node.obj.add_token(color, token_count)

            remove_token_color_name = self.remove_token_color_var.get().strip() if hasattr(self, "remove_token_color_var") else ""
            remove_token_count_text = self.remove_token_count_var.get().strip() if hasattr(self, "remove_token_count_var") else ""
            if remove_token_color_name:
                try:
                    remove_token_count = int(remove_token_count_text) if remove_token_count_text else 1
                except ValueError:
                    messagebox.showerror("Invalid token count", "Token count must be an integer")
                    return
                if remove_token_count <= 0:
                    messagebox.showerror("Invalid token count", "Token count must be greater than zero")
                    return
                color = self._resolve_color(remove_token_color_name)
                current_count = self.node.obj.get_token_count(color)
                if current_count < remove_token_count:
                    messagebox.showerror("Not enough tokens", f"Only {current_count} token(s) of that color are available")
                    return
                self.node.obj.remove_token(color, remove_token_count)

        if self.canvas.selected_node is self.node:
            self.canvas.select_node(self.node)
        self.destroy()


class NodeInfo:
    def __init__(self, obj, shape_id, label_id, node_type, x, y):
        self.obj = obj
        self.shape_id = shape_id
        self.label_id = label_id
        self.node_type = node_type
        self.x = x
        self.y = y


class NetCanvas(tk.Canvas):
    def __init__(self, parent, net, inspector, **kwargs):
        super().__init__(parent, bg="white", highlightthickness=1, highlightbackground="#999", **kwargs)
        self.net = net
        self.inspector = inspector
        self.toolbar = None
        self.nodes = []
        self.arcs = []
        self.mode = "select"
        self.pending_arc_source = None
        self.selected_node = None
        self.node_radius = 30
        self.grid_size = 20
        self.bind("<Button-1>", self.on_click)
        self.bind("<Double-Button-1>", self.on_double_click)
        self.bind("<Delete>", self.delete_selected_node)
        self.bind("<BackSpace>", self.delete_selected_node)
        self.bind("<Configure>", lambda event: self.draw_grid())
        self.draw_grid()

    def draw_grid(self):
        self.delete("grid")
        width = self.winfo_width() or 700
        height = self.winfo_height() or 650
        for x in range(0, width, self.grid_size):
            self.create_line(x, 0, x, height, fill="#e5e7eb", tags="grid")
        for y in range(0, height, self.grid_size):
            self.create_line(0, y, width, y, fill="#e5e7eb", tags="grid")
        self.tag_lower("grid")

    def set_mode(self, mode):
        self.mode = mode
        self.pending_arc_source = None
        self.inspector.update_mode(mode.capitalize())
        self.inspector.update_status(f"Mode: {mode}")
        if self.toolbar is not None:
            self.toolbar.update_mode(mode)

    def find_node_at(self, x, y):
        hits = self.find_overlapping(x, y, x, y)
        for item in hits:
            for node in self.nodes:
                if item in (node.shape_id, node.label_id):
                    return node
        return None

    def snap_point(self, x, y):
        return round(x / self.grid_size) * self.grid_size, round(y / self.grid_size) * self.grid_size

    def can_place_node(self, x, y, ignore_node=None):
        for node in self.nodes:
            if node is ignore_node:
                continue
            distance = ((x - node.x) ** 2 + (y - node.y) ** 2) ** 0.5
            if distance < self.node_radius * 2:
                return False
        return True

    def move_node(self, node, x, y):
        node.x = x
        node.y = y
        self.coords(node.shape_id, x - self.node_radius, y - self.node_radius, x + self.node_radius, y + self.node_radius)
        self.coords(node.label_id, x, y)
        for arc_id, source, target in self.arcs:
            if source is node or target is node:
                self.coords(arc_id, source.x, source.y, target.x, target.y)

    def delete_selected_node(self, event=None):
        self.delete_node(self.selected_node)

    def delete_node(self, node):
        if node is None:
            return

        for arc_id, source, target in list(self.arcs):
            if source is node or target is node:
                self.delete(arc_id)
                self.arcs.remove((arc_id, source, target))
                self.net.remove_arc_by_objects(source.obj, target.obj)

        self.delete(node.shape_id)
        self.delete(node.label_id)
        self.nodes.remove(node)
        self.update_selection_visuals()

        if node.node_type == "place":
            self.net.remove_place(node.obj)
        else:
            self.net.remove_transition(node.obj)

        if self.selected_node is node:
            self.selected_node = None
        self.inspector.update_status(f"Deleted {node.node_type} {node.obj.name}")

    def on_click(self, event):
        node = self.find_node_at(event.x, event.y)

        if self.mode == "place":
            self.create_place(event.x, event.y)
            return

        if self.mode == "transition":
            self.create_transition(event.x, event.y)
            return

        if self.mode == "arc":
            if node is None:
                return
            if self.pending_arc_source is None:
                self.pending_arc_source = node
                self.inspector.update_status(f"Arc source: {node.obj.name}")
            else:
                if node is self.pending_arc_source:
                    self.pending_arc_source = None
                    self.inspector.update_status("Arc creation canceled")
                    return
                self.create_arc(self.pending_arc_source, node)
                self.pending_arc_source = None
            return

        if self.mode == "select":
            self.select_node(node)
        elif node is None:
            self.select_node(None)

    def on_double_click(self, event):
        node = self.find_node_at(event.x, event.y)
        if node is None:
            return
        if node.node_type not in {"place", "transition"}:
            return
        self.select_node(node)
        NodeEditDialog(self, self, node)

    def update_selection_visuals(self):
        for node in self.nodes:
            if node is self.selected_node:
                self.itemconfig(node.shape_id, outline="#2563eb", width=3)
            else:
                self.itemconfig(node.shape_id, outline="#333", width=2)

    def select_node(self, node):
        self.selected_node = node
        self.update_selection_visuals()
        if node is None:
            self.inspector.show_message("No node selected")
            return
        name = node.obj.name
        node_type = node.node_type
        tokens = None
        enabled = None
        if node_type == "transition":
            enabled = self.net.is_enabled(node.obj)
        if node_type == "place":
            tokens = node.obj.tokens
        self.inspector.show_node(node_type, name, tokens, enabled)

    def create_place(self, x, y):
        x, y = self.snap_point(x, y)
        if not self.can_place_node(x, y):
            self.inspector.update_status("Cannot overlap places or transitions")
            return
        name = f"p{len([n for n in self.nodes if n.node_type == 'place']) + 1}"
        default_color = self.net.colors[0] if self.net.colors else None
        colors = [default_color] if default_color else None
        place = self.net.add_place(name, colors=colors)
        shape = self.create_oval(x - self.node_radius, y - self.node_radius, x + self.node_radius, y + self.node_radius, fill="#f8f8ff", outline="#333", width=2)
        label = self.create_text(x, y, text=name)
        self.nodes.append(NodeInfo(place, shape, label, "place", x, y))
        self.inspector.update_status(f"Created place {name}")

    def create_transition(self, x, y):
        x, y = self.snap_point(x, y)
        if not self.can_place_node(x, y):
            self.inspector.update_status("Cannot overlap places or transitions")
            return
        name = f"t{len([n for n in self.nodes if n.node_type == 'transition']) + 1}"
        default_color = self.net.colors[0] if self.net.colors else None
        colors = [default_color] if default_color else None
        transition = self.net.add_transition(name, colors=colors)
        shape = self.create_rectangle(x - self.node_radius, y - self.node_radius, x + self.node_radius, y + self.node_radius, fill="#fff8dc", outline="#333", width=2)
        label = self.create_text(x, y, text=name)
        self.nodes.append(NodeInfo(transition, shape, label, "transition", x, y))
        self.inspector.update_status(f"Created transition {name}")

    def create_arc(self, source_node, target_node):
        line = self.create_line(source_node.x, source_node.y, target_node.x, target_node.y, arrow=tk.LAST, width=2)
        self.arcs.append((line, source_node, target_node))
        self.net.add_arc(source_node.obj, target_node.obj, weight=1)
        self.inspector.update_status(f"Created arc {source_node.obj.name} -> {target_node.obj.name}")

    def redraw(self):
        pass
