import tkinter as tk

from GUI.Canvas import NetCanvas
from GUI.Inspector import Inspector
from GUI.Toolbar import Toolbar
from Model.ColoredPetriNet import ColoredPetriNet


def build_app():
    root = tk.Tk()
    root.title("PyPN")
    root.geometry("1000x700")

    net = ColoredPetriNet()

    inspector = Inspector(root, width=240, height=180)
    inspector.pack(side=tk.RIGHT, fill=tk.Y)

    toolbar = Toolbar(root, None)
    toolbar.pack(side=tk.LEFT, fill=tk.Y)

    canvas = NetCanvas(root, net, inspector, width=700, height=650)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=8, pady=8)

    toolbar.canvas = canvas
    canvas.toolbar = toolbar
    inspector.update_status("Ready")

    return root


if __name__ == "__main__":
    app = build_app()
    app.mainloop()
