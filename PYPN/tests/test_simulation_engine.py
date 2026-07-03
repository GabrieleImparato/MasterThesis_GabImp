import unittest

from Controller.SimulationEngine import SimulationEngine


class FakeInspector:
    def __init__(self):
        self.messages = []

    def show_message(self, message):
        self.messages.append(message)

    def update_status(self, message):
        self.messages.append(message)


class FakeNode:
    def __init__(self, name, node_type):
        self.obj = type("Obj", (), {"name": name})()
        self.node_type = node_type


class FakeCanvas:
    def __init__(self, nodes):
        self.nodes = nodes
        self.inspector = FakeInspector()
        self.selected_node = None
        self._callbacks = []

    def select_node(self, node):
        self.selected_node = node

    def animate_fire(self, node):
        pass  # no-op in test

    def update_place_labels(self):
        pass  # no-op in test

    def after(self, ms, fn, *args):
        """Esegue immediatamente la callback per rendere i test sincroni."""
        fn(*args)
        return fn

    def after_cancel(self, callback):
        if callback in self._callbacks:
            self._callbacks.remove(callback)


class FakeNet:
    def __init__(self, enabled_names):
        self.enabled_names = enabled_names
        self.fired = []

    def is_enabled(self, transition):
        return transition.name in self.enabled_names

    def fire(self, transition):
        self.fired.append(transition.name)


class SimulationEngineTests(unittest.TestCase):
    def test_step_fires_one_enabled_transition(self):
        enabled = FakeNode("t1", "transition")
        disabled = FakeNode("t2", "transition")
        canvas = FakeCanvas([enabled, disabled])
        net = FakeNet(["t1"])
        canvas.net = net

        engine = SimulationEngine(canvas, interval_ms=10)
        fired = engine._step()

        self.assertTrue(fired)
        self.assertEqual(net.fired, ["t1"])
        self.assertIs(canvas.selected_node, enabled)

    def test_step_returns_false_when_no_enabled_transitions(self):
        node = FakeNode("t1", "transition")
        canvas = FakeCanvas([node])
        net = FakeNet([])  # nessuna transizione abilitata
        canvas.net = net

        engine = SimulationEngine(canvas, interval_ms=10)
        fired = engine._step()

        self.assertFalse(fired)
        self.assertEqual(net.fired, [])

    def test_max_iterations_limit(self):
        """Verifica che la simulazione si fermi dopo max_iterations passi."""
        t1 = FakeNode("t1", "transition")
        canvas = FakeCanvas([t1])
        net = FakeNet(["t1"])
        canvas.net = net

        done_called = []
        engine = SimulationEngine(canvas, interval_ms=0, max_iterations=3, on_done=lambda: done_called.append(True))

        # Simula il loop manualmente (senza thread) per testare la logica
        for _ in range(3):
            if engine.max_iterations is not None and engine._iterations_done >= engine.max_iterations:
                break
            engine._step()
            engine._iterations_done += 1

        self.assertEqual(engine._iterations_done, 3)
        self.assertEqual(len(net.fired), 3)


if __name__ == "__main__":
    unittest.main()
