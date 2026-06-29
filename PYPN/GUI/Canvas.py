import tkinter as tk

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
        self.nodes = []
        self.arcs = []
        self.mode = "select"
        self.pending_arc_source = None
        self.selected_node = None
        self.node_radius = 30
        self.bind("<Button-1>", self.on_click)

    def set_mode(self, mode):
        self.mode = mode
        self.pending_arc_source = None
        self.selected_node = None
        self.inspector.update_status(f"Mode: {mode}")

    def find_node_at(self, x, y):
        hits = self.find_overlapping(x, y, x, y)
        for item in hits:
            for node in self.nodes:
                if item in (node.shape_id, node.label_id):
                    return node
        return None

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

    def select_node(self, node):
        self.selected_node = node
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
        name = f"p{len([n for n in self.nodes if n.node_type == 'place']) + 1}"
        default_color = self.net.colors[0] if self.net.colors else None
        colors = [default_color] if default_color else None
        place = self.net.add_place(name, colors=colors)
        shape = self.create_oval(x - self.node_radius, y - self.node_radius, x + self.node_radius, y + self.node_radius, fill="#f8f8ff", outline="#333", width=2)
        label = self.create_text(x, y, text=name)
        self.nodes.append(NodeInfo(place, shape, label, "place", x, y))
        self.inspector.update_status(f"Created place {name}")

    def create_transition(self, x, y):
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
