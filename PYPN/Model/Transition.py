
class Transition:
    def __init__(self, name, colors=None):
        self.name = name
        self.colors = set(colors) if colors else set()

    def add_allowed_color(self, color):
        self.colors.add(color)

    def __repr__(self):
        allowed = [getattr(c, 'name', c) for c in sorted(self.colors, key=lambda x: getattr(x, 'name', x))] if self.colors else None
        return f"Transition({self.name}, allowed_colors={allowed})"