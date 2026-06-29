from collections import Counter

class Arc:
    def __init__(self, start, end, weight=1, color_map=None):
        self.start = start
        self.end = end
        self.weight = int(weight)
        self.color_map = self._normalize_color_map(color_map)

    def _normalize_color_map(self, color_map):
        if color_map is None:
            return {}
        normalized = {}
        for source_color, target in color_map.items():
            if isinstance(target, Counter):
                normalized[source_color] = target
            elif isinstance(target, dict):
                normalized[source_color] = Counter(target)
            else:
                raise ValueError("Arc color_map must be a dict or Counter")
        return normalized

    def __repr__(self):
        s = getattr(self.start, 'name', self.start)
        e = getattr(self.end, 'name', self.end)
        return f"Arc({s}, {e}, {self.weight}, color_map={self.color_map})"