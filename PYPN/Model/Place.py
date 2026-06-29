from collections import Counter

class Place:
    def __init__(self, name, colors=None, tokens=None):
        self.name = name
        self.colors = set(colors) if colors else set()
        self.tokens = Counter()
        if tokens:
            # tokens expected as dict-like: {color: count}
            for c, n in tokens.items():
                self.add_token(c, n)

    def add_allowed_color(self, color):
        self.colors.add(color)

    def add_token(self, color, n=1):
        if self.colors and color not in self.colors:
            raise ValueError(f"Color {color} not allowed in place {self.name}")
        self.tokens[color] += n

    def remove_token(self, color, n=1):
        if self.tokens.get(color, 0) < n:
            raise ValueError("Not enough tokens to remove")
        self.tokens[color] -= n
        if self.tokens[color] == 0:
            del self.tokens[color]

    def remove_any(self, n):
        # remove up to n tokens, preferring most abundant colors
        if sum(self.tokens.values()) < n:
            raise ValueError("Not enough tokens to remove")
        removed = {}
        for color, cnt in sorted(self.tokens.items(), key=lambda x: -x[1]):
            if n <= 0:
                break
            take = min(cnt, n)
            self.remove_token(color, take)
            removed[color] = removed.get(color, 0) + take
            n -= take
        return removed

    def get_token_count(self, color):
        return self.tokens.get(color, 0)

    def total_tokens(self):
        return sum(self.tokens.values())

    def __repr__(self):
        allowed = [getattr(c, 'name', c) for c in sorted(self.colors, key=lambda x: getattr(x, 'name', x))] if self.colors else None
        tokens_repr = {getattr(c, 'name', c): v for c, v in self.tokens.items()}
        return f"Place({self.name}, allowed_colors={allowed}, tokens={tokens_repr})"