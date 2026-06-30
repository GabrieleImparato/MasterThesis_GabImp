import random
import threading
import time


class SimulationEngine:
    def __init__(self, canvas, interval_ms=1000):
        self.canvas = canvas
        self.interval_ms = interval_ms
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=0.2)
            self._thread = None

    def _run_loop(self):
        while self._running:
            self._step()
            time.sleep(self.interval_ms / 1000.0)

    def _step(self):
        if self.canvas is None:
            return

        enabled_transitions = [node for node in self.canvas.nodes if node.node_type == "transition" and self.canvas.net.is_enabled(node.obj)]
        if not enabled_transitions:
            self.canvas.inspector.show_message("No enabled transitions")
            return

        transition = random.choice(enabled_transitions)
        self.canvas.select_node(transition)
        self.canvas.net.fire(transition.obj)
        self.canvas.inspector.show_message(f"Auto-fired {transition.obj.name}")
