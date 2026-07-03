import tkinter as tk
from tkinter import messagebox

from Model.Color import DEFAULT_COLOR_NAME


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

        tk.Label(self, text="Allowed colors:").grid(row=3, column=0, sticky="nw", padx=8, pady=(4, 4))
        self.colors_listbox = tk.Listbox(self, selectmode=tk.MULTIPLE, height=5, exportselection=False)
        self.colors_listbox.grid(row=3, column=1, padx=8, pady=(4, 4), sticky="w")
        self.palette_colors = sorted(self.canvas.net.colors, key=lambda color: color.name)
        selected_colors = set(node.obj.colors)
        for index, color in enumerate(self.palette_colors):
            self.colors_listbox.insert(tk.END, color.name)
            if color in selected_colors:
                self.colors_listbox.selection_set(index)

        if node.node_type == "place":
            tk.Label(self, text="Tokens:").grid(row=4, column=0, sticky="nw", padx=8, pady=(8, 4))
            self.token_entries = {}
            token_frame = tk.Frame(self)
            token_frame.grid(row=4, column=1, columnspan=2, sticky="w", padx=8, pady=(8, 4))
            for index, color in enumerate(self.palette_colors):
                lbl = tk.Label(token_frame, text=f"{color.name}:")
                lbl.grid(row=index, column=0, sticky="e", pady=2)
                current_cnt = node.obj.get_token_count(color)
                var = tk.StringVar(value=str(current_cnt))
                ent = tk.Entry(token_frame, textvariable=var, width=8)
                ent.grid(row=index, column=1, sticky="w", padx=4, pady=2)
                self.token_entries[color] = var

        button_frame = tk.Frame(self)
        button_frame.grid(row=5, column=0, columnspan=3, pady=(8, 8))
        tk.Button(button_frame, text="Save", command=self.save).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="Delete", command=self.delete_node).pack(side=tk.LEFT, padx=4)
        tk.Button(button_frame, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=4)

        self.name_entry.focus_set()
        self.bind("<Return>", lambda event: self.save())
        self.bind("<Escape>", lambda event: self.destroy())

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

        selected_indexes = self.colors_listbox.curselection()
        self.node.obj.colors = {self.palette_colors[index] for index in selected_indexes}

        if self.node.node_type == "place":
            counts_to_set = {}
            for color, var in self.token_entries.items():
                try:
                    val_str = var.get().strip()
                    count_val = int(val_str) if val_str else 0
                except ValueError:
                    messagebox.showerror("Invalid token count", f"Token count for {color.name} must be an integer")
                    return
                if count_val < 0:
                    messagebox.showerror("Invalid token count", f"Token count for {color.name} cannot be negative")
                    return
                counts_to_set[color] = count_val

            self.node.obj.tokens.clear()
            for color, count_val in counts_to_set.items():
                if count_val > 0:
                    if color not in self.node.obj.colors:
                        self.node.obj.colors.add(color)
                    self.node.obj.add_token(color, count_val)

        if self.canvas.selected_node is self.node:
            self.canvas.select_node(self.node)

        self.canvas.update_place_labels()
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

    # Sostituisci il metodo create_place esistente con questo per includere (0) alla creazione
    def create_place(self, x, y):
        x, y = self.snap_point(x, y)
        if not self.can_place_node(x, y):
            self.inspector.update_status("Cannot overlap places or transitions")
            return
        name = f"p{len([n for n in self.nodes if n.node_type == 'place']) + 1}"
        default_color = self.net.get_color(DEFAULT_COLOR_NAME) if self.net.colors else None
        colors = [default_color] if default_color else None
        place = self.net.add_place(name, colors=colors)
        shape = self.create_oval(x - self.node_radius, y - self.node_radius, x + self.node_radius, y + self.node_radius, fill="#f8f8ff", outline="#333", width=2)
        
        # Mostra sia il nome che il numero di token totali iniziali (0)
        label = self.create_text(x, y, text=f"{name}\n(0)", justify="center")
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
        if hasattr(node, "label_bg_id"):
            self._fit_label_bg(node.label_id, node.label_bg_id)
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
        if hasattr(node, "label_bg_id"):
            self.delete(node.label_bg_id)
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
        default_color = self.net.get_color(DEFAULT_COLOR_NAME) if self.net.colors else None
        colors = [default_color] if default_color else None
        place = self.net.add_place(name, colors=colors)
        shape = self.create_oval(
            x - self.node_radius, y - self.node_radius,
            x + self.node_radius, y + self.node_radius,
            fill="#f0f4ff", outline="#2563eb", width=2
        )
        bg = self.create_rectangle(0, 0, 1, 1, fill="white", outline="", tags="label_bg")
        label = self.create_text(
            x, y, text=f"{name}\n(0)", justify="center",
            font=("Arial", 9, "bold"), fill="#111", tags="node_label"
        )
        self._fit_label_bg(label, bg)
        self.nodes.append(NodeInfo(place, shape, label, "place", x, y))
        self.nodes[-1].label_bg_id = bg
        self.inspector.update_status(f"Created place {name}")
        self.update_place_labels()

    def _fit_label_bg(self, label_id, bg_id):
        """Ridimensiona il rettangolo sfondo sotto il testo e lo porta sotto il testo."""
        self.update_idletasks()
        bbox = self.bbox(label_id)
        if bbox:
            pad = 2
            self.coords(bg_id, bbox[0] - pad, bbox[1] - pad, bbox[2] + pad, bbox[3] + pad)
        self.tag_lower(bg_id, label_id)

    def update_place_labels(self):
        for node in self.nodes:
            if node.node_type == "place":
                if isinstance(node.obj.tokens, dict):
                    total_tokens = sum(node.obj.tokens.values())
                else:
                    total_tokens = len(node.obj.tokens)
                self.itemconfigure(node.label_id, text=f"{node.obj.name}\n({total_tokens})")
                if hasattr(node, "label_bg_id"):
                    self._fit_label_bg(node.label_id, node.label_bg_id)
                self.tag_raise(node.label_id)

    def animate_fire(self, transition_node):
        involved_arcs = []
        for arc_id, source, target in self.arcs:
            if source is transition_node or target is transition_node:
                involved_arcs.append(arc_id)
                self.itemconfig(arc_id, fill="#e53e3e", width=3)

        self.update_place_labels()

        for node in self.nodes:
            if hasattr(node, "label_bg_id"):
                self.tag_raise(node.label_bg_id)
            self.tag_raise(node.label_id)

        if self.selected_node:
            self.select_node(self.selected_node)

        self.after(500, lambda: self.reset_arc_colors(involved_arcs))

    def reset_arc_colors(self, arc_ids):
        for arc_id in arc_ids:
            if arc_id in self.find_all():
                self.itemconfig(arc_id, fill="#555", width=2)

    def create_transition(self, x, y):
        x, y = self.snap_point(x, y)
        if not self.can_place_node(x, y):
            self.inspector.update_status("Cannot overlap places or transitions")
            return
        name = f"t{len([n for n in self.nodes if n.node_type == 'transition']) + 1}"
        default_color = self.net.get_color(DEFAULT_COLOR_NAME) if self.net.colors else None
        colors = [default_color] if default_color else None
        transition = self.net.add_transition(name, colors=colors)
        shape = self.create_rectangle(
            x - self.node_radius, y - self.node_radius,
            x + self.node_radius, y + self.node_radius,
            fill="#fffbea", outline="#d97706", width=2
        )
        bg = self.create_rectangle(0, 0, 1, 1, fill="white", outline="", tags="label_bg")
        label = self.create_text(
            x, y, text=name,
            font=("Arial", 9, "bold"), fill="#111", tags="node_label"
        )
        self._fit_label_bg(label, bg)
        node_info = NodeInfo(transition, shape, label, "transition", x, y)
        node_info.label_bg_id = bg
        self.nodes.append(node_info)
        self.inspector.update_status(f"Created transition {name}")

    def create_arc(self, source_node, target_node):
        line = self.create_line(
            source_node.x, source_node.y, target_node.x, target_node.y,
            arrow=tk.LAST, width=2, fill="#555", arrowshape=(10, 12, 4)
        )
        self.arcs.append((line, source_node, target_node))
        self.net.add_arc(source_node.obj, target_node.obj, weight=1)
        self.inspector.update_status(f"Created arc {source_node.obj.name} -> {target_node.obj.name}")
        # Porta subito tutte le label sopra all'arco appena disegnato
        for node in self.nodes:
            if hasattr(node, "label_bg_id"):
                self.tag_raise(node.label_bg_id)
            self.tag_raise(node.label_id)

    def redraw(self):
        pass


class AnalysisResultDialog(tk.Toplevel):
    def __init__(self, parent, title, content):
        super().__init__(parent)
        self.title(title)
        self.geometry("750x550")
        self.minsize(500, 400)
        self.transient(parent)
        
        header = tk.Label(self, text=title, font=("Arial", 12, "bold"), fg="#2563eb", pady=8)
        header.pack(fill=tk.X)
        
        frame = tk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)
        
        ysb = tk.Scrollbar(frame, orient=tk.VERTICAL)
        xsb = tk.Scrollbar(frame, orient=tk.HORIZONTAL)
        
        self.text_widget = tk.Text(frame, wrap=tk.NONE, font=("Courier New", 10),
                                   xscrollcommand=xsb.set, yscrollcommand=ysb.set,
                                   bg="#fdfdfd", fg="#222")
        
        ysb.config(command=self.text_widget.yview)
        xsb.config(command=self.text_widget.xview)
        
        ysb.pack(side=tk.RIGHT, fill=tk.Y)
        xsb.pack(side=tk.BOTTOM, fill=tk.X)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.text_widget.insert(tk.END, content)
        self.text_widget.config(state=tk.DISABLED)
        
        button_frame = tk.Frame(self, pady=8)
        button_frame.pack(fill=tk.X)
        tk.Button(button_frame, text="Close", command=self.destroy, width=12).pack()
        
        self.bind("<Escape>", lambda event: self.destroy())
