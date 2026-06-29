from .Color import Color
from .Place import Place

class Token:
    def __init__(self, color: Color, place: Place):
        self.color = color
        self.place = place

    def __repr__(self):
        cname = getattr(self.color, 'name', self.color)
        pname = getattr(self.place, 'name', self.place)
        return f"Token({cname}, {pname})"