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

    def after(self, ms, callback):
        self._callbacks.append(callback)
        return callback

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
        engine._step()

        self.assertEqual(net.fired, ["t1"])
        self.assertIs(canvas.selected_node, enabled)


if __name__ == "__main__":
    unittest.main()
