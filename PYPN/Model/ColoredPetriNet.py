from collections import Counter

from .Arc import Arc
from .Transition import Transition
from .Color import Color, PREDEFINED_COLOR_NAMES
from .Place import Place

class ColoredPetriNet:
    def __init__(self):
        self.arcs = []
        self.transitions = []
        self.places = []
        self.colors = [Color(name) for name in PREDEFINED_COLOR_NAMES]

    def add_place(self, name, colors=None):
        p = Place(name, colors=colors)
        self.places.append(p)
        return p

    def add_color(self, name):
        if name not in PREDEFINED_COLOR_NAMES:
            raise ValueError(f"Color {name} is not in the predefined palette")
        existing = self.get_color(name)
        if existing is not None:
            return existing
        c = Color(name)
        self.colors.append(c)
        return c

    def get_color(self, name):
        return next((color for color in self.colors if color.name == name), None)

    def add_transition(self, name, colors=None):
        t = Transition(name, colors=colors)
        self.transitions.append(t)
        return t

    def add_arc(self, start, end, weight=1, color_map=None):
        arc = Arc(start, end, weight, color_map=color_map)
        self.arcs.append(arc)
        return arc

    def remove_arc_by_objects(self, start, end):
        self.arcs = [arc for arc in self.arcs if not (arc.start is start and arc.end is end)]

    def remove_place(self, place):
        self.places = [p for p in self.places if p is not place]
        self.arcs = [arc for arc in self.arcs if arc.start is not place and arc.end is not place]

    def remove_transition(self, transition):
        self.transitions = [t for t in self.transitions if t is not transition]
        self.arcs = [arc for arc in self.arcs if arc.start is not transition and arc.end is not transition]

    def add_token(self, place, color, n=1):
        place.add_token(color, n)

    def get_input_arcs(self, transition):
        return [a for a in self.arcs if a.end is transition]

    def get_output_arcs(self, transition):
        return [a for a in self.arcs if a.start is transition]

    def _build_fire_plan(self, transition):
        place_tokens = {place: Counter(place.tokens) for place in self.places}
        removals = []
        additions = []
        transition_tokens = Counter()

        for arc in self.get_input_arcs(transition):
            available = place_tokens[arc.start]
            if arc.color_map:
                for source_color, target_multiset in arc.color_map.items():
                    count = sum(target_multiset.values()) * arc.weight
                    if available.get(source_color, 0) < count:
                        raise RuntimeError("Transition not enabled")
                    available[source_color] -= count
                    if available[source_color] == 0:
                        del available[source_color]
                    removals.append((arc.start, source_color, count))
                    for t_color, t_count in target_multiset.items():
                        transition_tokens[t_color] += t_count * arc.weight
            else:
                # --- CORREZIONE: Confronto basato sul nome del colore ---
                if transition.colors:
                    # Estraiamo i nomi dei colori ammessi dalla transizione
                    allowed_names = {c.name for c in transition.colors}
                    # Filtriamo i gettoni disponibili nel posto che hanno un nome compatibile
                    valid_available_tokens = {
                        color: count for color, count in available.items() if color.name in allowed_names
                    }
                else:
                    # Se la transizione non ha vincoli di colore, può usare tutto
                    valid_available_tokens = dict(available)
                
                # Controlliamo se la somma dei gettoni del colore CORRETTO è sufficiente
                if sum(valid_available_tokens.values()) < arc.weight:
                    raise RuntimeError(f"Transition {transition.name} not enabled: missing matching colored tokens")
                
                remaining = arc.weight
                # Consumiamo i gettoni partendo da quelli del colore richiesto maggiormente presente
                for color, count in sorted(list(valid_available_tokens.items()), key=lambda item: -item[1]):
                    if remaining <= 0:
                        break
                    take = min(count, remaining)
                    available[color] -= take
                    if available[color] == 0:
                        del available[color]
                    removals.append((arc.start, color, take))
                    transition_tokens[color] += take
                    remaining -= take

        for arc in self.get_output_arcs(transition):
            if arc.color_map:
                for t_color, place_multiset in arc.color_map.items():
                    t_count = transition_tokens.get(t_color, 0)
                    if t_count <= 0:
                        continue
                    for p_color, p_count in place_multiset.items():
                        count = p_count * t_count
                        self._validate_place_accepts(arc.end, p_color)
                        additions.append((arc.end, p_color, count))
            else:
                for color, count in transition_tokens.items():
                    self._validate_place_accepts(arc.end, color)
                    additions.append((arc.end, color, count))

        return removals, additions

    def _validate_place_accepts(self, place, color):
        if place.colors and color not in place.colors:
            raise RuntimeError(f"Color {color.name} not allowed in place {place.name}")

    def is_enabled(self, transition):
        try:
            self._build_fire_plan(transition)
        except RuntimeError:
            return False
        return True

    def fire(self, transition):
        removals, additions = self._build_fire_plan(transition)
        for place, color, count in removals:
            place.remove_token(color, count)
        for place, color, count in additions:
            place.add_token(color, count)

    def __repr__(self):
        return f"ColoredPetriNet(Places: {self.places}, Transitions: {self.transitions}, Arcs: {self.arcs}, Colors: {self.colors})"
