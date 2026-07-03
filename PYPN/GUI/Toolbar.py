import tkinter as tk

from Controller.SimulationEngine import SimulationEngine
from Controller.AnalysisEngine import AnalysisEngine
from GUI.Canvas import AnalysisResultDialog


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
            ("Run", [("Fire transition", "fire"), ("Simulate", "auto"), ("Stop", "stop_auto"), ("Delete selected", "delete"), ("Reset", "reset")]),
            ("Analyze", [("Show matrices", "matrices"), ("P/T Invariants", "invariants"), ("Coverability Tree", "coverability")]),
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
        if mode == "matrices":
            self.show_matrices()
            return
        if mode == "invariants":
            self.show_invariants()
            return
        if mode == "coverability":
            self.show_coverability_tree()
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
        """Apre il dialogo di configurazione e avvia la simulazione."""
        if self.simulation_engine is not None and self.simulation_engine.is_running:
            self.canvas.inspector.show_message("Simulazione già in corso")
            return
        SimulationConfigDialog(self.winfo_toplevel(), self)

    def _launch_simulation(self, max_iterations, interval_ms):
        """Avviata dal dialogo di configurazione."""
        if self.canvas is None:
            return
        self.simulation_engine = SimulationEngine(
            self.canvas,
            interval_ms=interval_ms,
            max_iterations=max_iterations,
            on_done=self._on_simulation_done,
        )
        self.simulation_engine.start()
        mode_str = "∞ iterazioni" if max_iterations is None else f"{max_iterations} iterazioni"
        self.canvas.inspector.show_message(f"Simulazione avviata — {mode_str}, {interval_ms} ms/step")

    def _on_simulation_done(self):
        """Callback chiamata dal SimulationEngine al termine."""
        pass  # Il messaggio di fine è già mostrato dal engine

    def stop_auto_simulation(self):
        if self.simulation_engine is not None:
            self.simulation_engine.stop()
            # Ripristina la marcatura iniziale anche in caso di stop manuale
            self.simulation_engine._restore_marking()
            self.simulation_engine = None
        if self.canvas is not None:
            self.canvas.update_place_labels()
            self.canvas.inspector.show_message("Simulazione fermata — rete ripristinata")


    def fire_transition(self):
        node = self.canvas.selected_node
        if node is None or node.node_type != "transition":
            self.canvas.inspector.show_message("Select a transition to fire")
            return
        try:
            if self.canvas.net.is_enabled(node.obj):
                self.canvas.net.fire(node.obj)
                self.canvas.inspector.show_message(f"Fired {node.obj.name}")
                
                # --- NUOVO: Avvia animazione archi e aggiorna i contatori dei gettoni ---
                self.canvas.animate_fire(node)
                
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

    def show_matrices(self):
        if self.canvas is None:
            return
        try:
            engine = AnalysisEngine(self.canvas.net)
            content = engine.format_matrices()
            AnalysisResultDialog(self.winfo_toplevel(), "Pre, Post & Incidence Matrices", content)
        except Exception as exc:
            self.canvas.inspector.show_message(f"Analysis error: {str(exc)}")

    def show_invariants(self):
        if self.canvas is None:
            return
        try:
            engine = AnalysisEngine(self.canvas.net)
            content = engine.format_invariants()
            AnalysisResultDialog(self.winfo_toplevel(), "P & T Invariants", content)
        except Exception as exc:
            self.canvas.inspector.show_message(f"Analysis error: {str(exc)}")

    def show_coverability_tree(self):
        if self.canvas is None:
            return
        try:
            engine = AnalysisEngine(self.canvas.net)
            content = engine.format_coverability_tree()
            AnalysisResultDialog(self.winfo_toplevel(), "Coverability Tree (Karp-Miller)", content)
        except Exception as exc:
            self.canvas.inspector.show_message(f"Analysis error: {str(exc)}")


# ─────────────────────────────────────────────────────────────────────────────
# Dialog di configurazione simulazione
# ─────────────────────────────────────────────────────────────────────────────

class SimulationConfigDialog(tk.Toplevel):
    """
    Dialog modale che chiede all'utente:
      - Modalità: infinita oppure numero fisso di iterazioni
      - Intervallo tra gli step (ms)
    e avvia la simulazione tramite toolbar._launch_simulation().
    """

    def __init__(self, parent, toolbar):
        super().__init__(parent)
        self.toolbar = toolbar
        self.title("Configura Simulazione")
        self.transient(parent)
        self.resizable(False, False)
        self.grab_set()  # blocca interazione con la finestra principale

        # ── Modalità ──────────────────────────────────────────────────────────
        mode_frame = tk.LabelFrame(self, text="Modalità", padx=8, pady=6)
        mode_frame.grid(row=0, column=0, columnspan=2, padx=12, pady=(12, 6), sticky="ew")

        self.mode_var = tk.StringVar(value="infinite")

        tk.Radiobutton(
            mode_frame, text="Infinita  ∞", variable=self.mode_var,
            value="infinite", command=self._on_mode_change
        ).grid(row=0, column=0, sticky="w", pady=2)

        tk.Radiobutton(
            mode_frame, text="Numero fisso di iterazioni:", variable=self.mode_var,
            value="fixed", command=self._on_mode_change
        ).grid(row=1, column=0, sticky="w", pady=2)

        self.iter_var = tk.StringVar(value="10")
        self.iter_entry = tk.Entry(mode_frame, textvariable=self.iter_var, width=8, state=tk.DISABLED)
        self.iter_entry.grid(row=1, column=1, sticky="w", padx=4, pady=2)

        # ── Intervallo ────────────────────────────────────────────────────────
        tk.Label(self, text="Intervallo tra step (ms):").grid(
            row=1, column=0, sticky="e", padx=(12, 4), pady=6
        )
        self.interval_var = tk.StringVar(value="500")
        tk.Entry(self, textvariable=self.interval_var, width=8).grid(
            row=1, column=1, sticky="w", padx=(0, 12), pady=6
        )

        # ── Bottoni ───────────────────────────────────────────────────────────
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=(4, 12))

        tk.Button(btn_frame, text="▶  Avvia", width=10, command=self._launch).pack(side=tk.LEFT, padx=6)
        tk.Button(btn_frame, text="Annulla", width=10, command=self.destroy).pack(side=tk.LEFT, padx=6)

        self.bind("<Return>", lambda _: self._launch())
        self.bind("<Escape>", lambda _: self.destroy())

    def _on_mode_change(self):
        if self.mode_var.get() == "fixed":
            self.iter_entry.config(state=tk.NORMAL)
        else:
            self.iter_entry.config(state=tk.DISABLED)

    def _launch(self):
        # Validazione intervallo
        try:
            interval_ms = int(self.interval_var.get())
            if interval_ms < 10:
                raise ValueError
        except ValueError:
            tk.messagebox.showerror("Valore non valido", "L'intervallo deve essere un intero ≥ 10 ms", parent=self)
            return

        # Validazione iterazioni
        max_iterations = None
        if self.mode_var.get() == "fixed":
            try:
                max_iterations = int(self.iter_var.get())
                if max_iterations < 1:
                    raise ValueError
            except ValueError:
                tk.messagebox.showerror(
                    "Valore non valido", "Il numero di iterazioni deve essere un intero ≥ 1", parent=self
                )
                return

        self.destroy()
        self.toolbar._launch_simulation(max_iterations, interval_ms)

