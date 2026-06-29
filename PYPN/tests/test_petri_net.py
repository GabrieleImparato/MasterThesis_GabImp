import unittest

from Model.ColoredPetriNet import ColoredPetriNet


class PetriNetTests(unittest.TestCase):
    def test_cycle_transfers_token_back_to_origin(self):
        net = ColoredPetriNet()
        color = net.add_color("default")
        p1 = net.add_place("p1", colors=[color])
        p2 = net.add_place("p2", colors=[color])
        t1 = net.add_transition("t1", colors=[color])
        t2 = net.add_transition("t2", colors=[color])

        p1.add_token(color, 1)
        net.add_arc(p1, t1, weight=1)
        net.add_arc(t1, p2, weight=1)
        net.add_arc(p2, t2, weight=1)
        net.add_arc(t2, p1, weight=1)

        net.fire(t1)
        net.fire(t2)

        self.assertEqual(p1.get_token_count(color), 1)
        self.assertEqual(p2.get_token_count(color), 0)

    def test_remove_place_removes_associated_arcs(self):
        net = ColoredPetriNet()
        color = net.add_color("default")
        p1 = net.add_place("p1", colors=[color])
        t1 = net.add_transition("t1", colors=[color])
        net.add_arc(p1, t1, weight=1)

        net.remove_place(p1)

        self.assertNotIn(p1, net.places)
        self.assertEqual([arc for arc in net.arcs if arc.start is p1 or arc.end is p1], [])


if __name__ == "__main__":
    unittest.main()
