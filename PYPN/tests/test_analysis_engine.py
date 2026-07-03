import unittest
from Model.ColoredPetriNet import ColoredPetriNet
from Controller.AnalysisEngine import AnalysisEngine


class AnalysisEngineTests(unittest.TestCase):
    def test_matrix_dimensions_and_values(self):
        # Create a simple cycle net: p1 -> t1 -> p2 -> t2 -> p1
        net = ColoredPetriNet()
        color = net.get_color("black")
        
        p1 = net.add_place("p1", colors=[color])
        p2 = net.add_place("p2", colors=[color])
        t1 = net.add_transition("t1", colors=[color])
        t2 = net.add_transition("t2", colors=[color])

        net.add_arc(p1, t1, weight=1)
        net.add_arc(t1, p2, weight=1)
        net.add_arc(p2, t2, weight=2)  # different weight to test Pre/Post values
        net.add_arc(t2, p1, weight=1)

        engine = AnalysisEngine(net)

        # Unfolded places: p1 (black), p2 (black)
        self.assertEqual(len(engine.unfolded_places), 2)
        # Unfolded transitions: t1 (black), t2 (black)
        self.assertEqual(len(engine.unfolded_transitions), 2)

        # Check Pre and Post matrices
        # Places order: p1, p2 (sorted alphabetically by name)
        # Transitions order: t1, t2 (sorted alphabetically)
        # Pre:
        # p1 -> t1 (weight 1), p1 -> t2 (no arc)
        # p2 -> t1 (no arc), p2 -> t2 (weight 2)
        self.assertEqual(engine.Pre[0][0], 1)  # p1 -> t1
        self.assertEqual(engine.Pre[0][1], 0)  # p1 -> t2
        self.assertEqual(engine.Pre[1][0], 0)  # p2 -> t1
        self.assertEqual(engine.Pre[1][1], 2)  # p2 -> t2

        # Post:
        # t1 -> p1 (no arc), t1 -> p2 (weight 1)
        # t2 -> p1 (weight 1), t2 -> p2 (no arc)
        self.assertEqual(engine.Post[0][0], 0)  # t1 -> p1
        self.assertEqual(engine.Post[0][1], 1)  # t2 -> p1
        self.assertEqual(engine.Post[1][0], 1)  # t1 -> p2
        self.assertEqual(engine.Post[1][1], 0)  # t2 -> p2

        # Incidence: C = Post - Pre
        # C[0][0] = 0 - 1 = -1
        # C[0][1] = 1 - 0 = 1
        # C[1][0] = 1 - 0 = 1
        # C[1][1] = 0 - 2 = -2
        self.assertEqual(engine.C[0][0], -1)
        self.assertEqual(engine.C[0][1], 1)
        self.assertEqual(engine.C[1][0], 1)
        self.assertEqual(engine.C[1][1], -2)

    def test_invariants_calculation(self):
        # A simple net with a known P-invariant and T-invariant:
        # p1 -> t1 -> p2 -> t2 -> p1 (all weight 1)
        net = ColoredPetriNet()
        color = net.get_color("black")
        
        p1 = net.add_place("p1", colors=[color])
        p2 = net.add_place("p2", colors=[color])
        t1 = net.add_transition("t1", colors=[color])
        t2 = net.add_transition("t2", colors=[color])

        net.add_arc(p1, t1, weight=1)
        net.add_arc(t1, p2, weight=1)
        net.add_arc(p2, t2, weight=1)
        net.add_arc(t2, p1, weight=1)

        engine = AnalysisEngine(net)

        p_invs = engine.get_p_invariants()
        t_invs = engine.get_t_invariants()

        # There should be exactly one P-invariant: 1*p1 + 1*p2 = const
        self.assertEqual(len(p_invs), 1)
        self.assertEqual(p_invs[0], [1, 1])

        # There should be exactly one T-invariant: 1*t1 + 1*t2 = cycle
        self.assertEqual(len(t_invs), 1)
        self.assertEqual(t_invs[0], [1, 1])

    def test_coverability_tree(self):
        # Create a simple net p1 -> t1 -> p2, with 1 token in p1
        net = ColoredPetriNet()
        color = net.get_color("black")
        
        p1 = net.add_place("p1", colors=[color])
        p2 = net.add_place("p2", colors=[color])
        t1 = net.add_transition("t1", colors=[color])

        net.add_arc(p1, t1, weight=1)
        net.add_arc(t1, p2, weight=1)

        p1.add_token(color, 1)

        engine = AnalysisEngine(net)
        root = engine.compute_coverability_tree()

        self.assertIsNotNone(root)
        # Root marking: p1=1, p2=0
        self.assertEqual(root.marking[(p1, color)], 1)
        self.assertEqual(root.marking[(p2, color)], 0)

        # Children: one child representing after firing t1 (p1=0, p2=1)
        self.assertEqual(len(root.children), 1)
        child = root.children[0]
        self.assertEqual(child.marking[(p1, color)], 0)
        self.assertEqual(child.marking[(p2, color)], 1)
        # Since p1=0 now, t1 is no longer enabled, so child has no children
        self.assertEqual(len(child.children), 0)


if __name__ == "__main__":
    unittest.main()
