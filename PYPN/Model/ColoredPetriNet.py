from collections import Counter

from .Arc import Arc
from .Transition import Transition
from .Color import Color
from .Place import Place

class ColoredPetriNet:
    def __init__(self):
        self.arcs = []
        self.transitions = []
        self.places = []
        self.colors = []

    def add_place(self, name, colors=None):
        p = Place(name, colors=colors)
        self.places.append(p)
        return p

    def add_color(self, name):
        c = Color(name)
        self.colors.append(c)
        return c

    def add_transition(self, name, colors=None):
        t = Transition(name, colors=colors)
        self.transitions.append(t)
        return t

    def add_arc(self, start, end, weight=1, color_map=None):
        arc = Arc(start, end, weight, color_map=color_map)
        self.arcs.append(arc)
        return arc

    def add_token(self, place, color, n=1):
        place.add_token(color, n)

    def get_input_arcs(self, transition):
        return [a for a in self.arcs if a.end is transition]

    def get_output_arcs(self, transition):
        return [a for a in self.arcs if a.start is transition]

    def is_enabled(self, transition):
        for arc in self.get_input_arcs(transition):
            if arc.color_map:
                for source_color, target_multiset in arc.color_map.items():
                    required = sum(target_multiset.values()) * arc.weight
                    if arc.start.get_token_count(source_color) < required:
                        return False
            else:
                if arc.start.total_tokens() < arc.weight:
                    return False
        return True

    def fire(self, transition):
        if not self.is_enabled(transition):
            raise RuntimeError("Transition not enabled")
        transition_tokens = Counter()
        for arc in self.get_input_arcs(transition):
            if arc.color_map:
                for source_color, target_multiset in arc.color_map.items():
                    count = sum(target_multiset.values()) * arc.weight
                    arc.start.remove_token(source_color, count)
                    for t_color, t_count in target_multiset.items():
                        transition_tokens[t_color] += t_count * arc.weight
            else:
                removed = arc.start.remove_any(arc.weight)
                for c, cnt in removed.items():
                    transition_tokens[c] += cnt

        for arc in self.get_output_arcs(transition):
            if arc.color_map:
                for t_color, place_multiset in arc.color_map.items():
                    t_count = transition_tokens.get(t_color, 0)
                    if t_count <= 0:
                        continue
                    for p_color, p_count in place_multiset.items():
                        arc.end.add_token(p_color, p_count * t_count)
            else:
                for c, cnt in transition_tokens.items():
                    arc.end.add_token(c, cnt)

    def __repr__(self):
        return f"ColoredPetriNet(Places: {self.places}, Transitions: {self.transitions}, Arcs: {self.arcs}, Colors: {self.colors})"