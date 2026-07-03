import random
import threading


class SimulationEngine:
    """
    Esegue la simulazione automatica di una Petri Net colorata.

    Parametri:
        canvas: il widget NetCanvas che contiene la rete.
        interval_ms: intervallo in millisecondi tra uno scatto e il successivo.
        max_iterations: numero massimo di iterazioni (None = infinito).
        on_done: callback opzionale chiamata al termine della simulazione.
    """

    def __init__(self, canvas, interval_ms=1000, max_iterations=None, on_done=None):
        self.canvas = canvas
        self.interval_ms = interval_ms
        self.max_iterations = max_iterations  # None = infinito
        self.on_done = on_done
        self._running = False
        self._thread = None
        self._iterations_done = 0

    # ------------------------------------------------------------------ #
    # Controllo ciclo vita                                                  #
    # ------------------------------------------------------------------ #

    def start(self):
        """Avvia la simulazione in un thread demone."""
        if self._running:
            return
        self._snapshot_marking()   # salva lo stato iniziale
        self._running = True
        self._iterations_done = 0
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Ferma la simulazione il prima possibile."""
        self._running = False
        # Non joinare con timeout alto: il thread è daemon e il wait bloccherebbe la GUI
        self._thread = None

    @property
    def is_running(self):
        return self._running

    # ------------------------------------------------------------------ #
    # Loop principale (eseguito nel thread secondario)                     #
    # ------------------------------------------------------------------ #

    def _run_loop(self):
        while self._running:
            # Controlla limite iterazioni
            if self.max_iterations is not None and self._iterations_done >= self.max_iterations:
                self._schedule_gui(self._on_simulation_ended, "Max iterations reached")
                break

            fired = self._step()

            if not fired:
                # Nessuna transizione abilitata: blocco
                self._schedule_gui(self._on_simulation_ended, "No enabled transitions — simulation stopped")
                break

            self._iterations_done += 1

            # Attesa interrompibile: controlla _running ogni 50ms
            elapsed = 0
            step_ms = min(50, self.interval_ms)
            while elapsed < self.interval_ms and self._running:
                import time
                time.sleep(step_ms / 1000.0)
                elapsed += step_ms

        # Se siamo usciti per stop() esterno, non c'è nulla da notificare

    # ------------------------------------------------------------------ #
    # Singolo passo di simulazione                                         #
    # ------------------------------------------------------------------ #

    def _step(self):
        """
        Sceglie casualmente una transizione abilitata, la scatta,
        aggiorna la GUI nel thread corretto tramite canvas.after().
        Restituisce True se ha scattato, False se nessuna transizione è abilitata.
        """
        if self.canvas is None:
            return False

        enabled = [
            node for node in self.canvas.nodes
            if node.node_type == "transition" and self.canvas.net.is_enabled(node.obj)
        ]

        if not enabled:
            return False

        chosen = random.choice(enabled)
        self.canvas.net.fire(chosen.obj)
        iteration_label = (
            f"Step {self._iterations_done + 1}"
            if self.max_iterations is None
            else f"Step {self._iterations_done + 1}/{self.max_iterations}"
        )

        # Aggiornamenti GUI schedulati nel main thread
        self._schedule_gui(self._gui_update, chosen, iteration_label)
        return True

    # ------------------------------------------------------------------ #
    # Callback GUI (eseguite nel main thread via canvas.after)            #
    # ------------------------------------------------------------------ #

    def _schedule_gui(self, fn, *args):
        """Esegue `fn(*args)` nel main thread Tk."""
        if self.canvas is not None:
            self.canvas.after(0, fn, *args)

    def _gui_update(self, node, label):
        """Aggiorna selezione, etichette e animazione nel main thread."""
        if self.canvas is None:
            return
        self.canvas.select_node(node)
        self.canvas.animate_fire(node)
        self.canvas.inspector.show_message(f"Auto-fired {node.obj.name} — {label}")

    def _on_simulation_ended(self, reason):
        """Chiamata nel main thread al termine della simulazione."""
        self._running = False
        if self.canvas is not None:
            self._restore_marking()           # ripristina lo stato iniziale
            self.canvas.update_place_labels() # aggiorna le etichette dei token
            self.canvas.inspector.show_message(f"{reason} — rete ripristinata")
        if self.on_done is not None:
            self.on_done()

    # ------------------------------------------------------------------ #
    # Snapshot / Restore della marcatura iniziale                         #
    # ------------------------------------------------------------------ #

    def _snapshot_marking(self):
        """Cattura i token correnti di tutti i posti."""
        from collections import Counter
        self._initial_marking = {}
        if self.canvas is None:
            return
        for node in self.canvas.nodes:
            if node.node_type == "place":
                # Copia profonda del Counter dei token
                self._initial_marking[node.obj] = Counter(node.obj.tokens)

    def _restore_marking(self):
        """Ripristina i token allo snapshot salvato prima della simulazione."""
        if not hasattr(self, "_initial_marking") or self.canvas is None:
            return
        for node in self.canvas.nodes:
            if node.node_type == "place":
                place = node.obj
                place.tokens.clear()
                saved = self._initial_marking.get(place)
                if saved:
                    for color, count in saved.items():
                        place.tokens[color] = count
