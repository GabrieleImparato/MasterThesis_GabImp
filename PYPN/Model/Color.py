from enum import Enum

class Color:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f"Color({self.name})"
    def __eq__(self, other):
        return isinstance(other, Color) and self.name == other.name

    def __hash__(self):
        return hash(self.name)