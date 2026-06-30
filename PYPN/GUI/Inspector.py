import tkinter as tk


class Inspector(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bd=1, relief=tk.SUNKEN, **kwargs)
        self.title = tk.Label(self, text="Inspector", font=("Arial", 10, "bold"))
        self.title.pack(anchor="w", padx=4, pady=(4, 0))
        self.mode = tk.Label(self, text="Mode: select", fg="#2563eb", anchor="w")
        self.mode.pack(anchor="w", padx=4, pady=(2, 0))
        self.text = tk.Label(self, text="Select a place or transition", justify="left", anchor="w")
        self.text.pack(fill="both", expand=True, padx=4, pady=4)
        self.status = tk.Label(self, text="Ready", fg="#555", anchor="w")
        self.status.pack(fill="x", padx=4, pady=(0, 4))

    def show_node(self, node_type, name, tokens, enabled):
        result = [f"Type: {node_type}", f"Name: {name}"]
        if tokens is not None:
            token_text = ", ".join(f"{getattr(c, 'name', c)}={count}" for c, count in tokens.items()) or "empty"
            result.append(f"Tokens: {token_text}")
        if enabled is not None:
            result.append(f"Enabled: {enabled}")
        self.text.config(text="\n".join(result))
        self.status.config(text=f"Selected {name}")

    def show_message(self, message):
        self.text.config(text=message)
        self.status.config(text="Info")

    def update_status(self, message):
        self.status.config(text=message)

    def update_mode(self, mode):
        self.mode.config(text=f"Mode: {mode}")
