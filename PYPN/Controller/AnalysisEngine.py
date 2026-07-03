import math
from collections import Counter

class CoverabilityNode:
    def __init__(self, marking, parent=None, transition_fired=None):
        self.marking = marking  # dict: (place, color) -> int or float('inf')
        self.parent = parent
        self.transition_fired = transition_fired  # tuple: (t, tc)
        self.children = []


def minimal_invariants(C):
    """
    Computes the minimal support non-negative invariants for a matrix C using the
    Martinez-Silva (Fourier-Motzkin elimination) algorithm.
    Solves: C * x = 0, with x >= 0 and x != 0.
    """
    m = len(C)
    n = len(C[0]) if m > 0 else 0
    if n == 0:
        return []

    # Initial matrix D: each row is [u_i, C[:, i]]
    D = []
    for i in range(n):
        row = [0] * n
        row[i] = 1
        for j in range(m):
            row.append(C[j][i])
        D.append(row)

    # Eliminate columns corresponding to places (indices n to n + m - 1)
    for col in range(n, n + m):
        P = []
        N = []
        Z = []
        for row in D:
            val = row[col]
            if val > 0:
                P.append(row)
            elif val < 0:
                N.append(row)
            else:
                Z.append(row)

        new_D = list(Z)

        # Combine positive and negative rows
        for rp in P:
            for rn in N:
                vp = rp[col]
                vn = rn[col]
                
                # Coefficients to eliminate the column value
                alpha = -vn
                beta = vp

                # Combine the rows
                new_row = [alpha * rp[k] + beta * rn[k] for k in range(len(rp))]

                # Reduce by GCD of transition coefficients (first n elements)
                coeffs = new_row[:n]
                # Filter out zeroes to compute gcd, or handle zero coefficients
                non_zero_coeffs = [abs(x) for x in coeffs if x != 0]
                if non_zero_coeffs:
                    g = non_zero_coeffs[0]
                    for val in non_zero_coeffs[1:]:
                        g = math.gcd(g, val)
                    if g > 1:
                        new_row = [val // g for val in new_row]

                # Support minimality check
                support = {k for k in range(n) if new_row[k] > 0}
                if not support:
                    continue

                is_minimal = True
                # Check against other rows in new_D
                for row_d in new_D:
                    support_d = {k for k in range(n) if row_d[k] > 0}
                    if support_d.issubset(support) and support_d != support:
                        is_minimal = False
                        break

                if is_minimal:
                    # Clean up rows in new_D that are now non-minimal compared to support
                    new_D = [r for r in new_D if not support.issubset({k for k in range(n) if r[k] > 0}) or {k for k in range(n) if r[k] > 0} == support]
                    # Avoid exact duplicate rows
                    if not any(r[:n] == new_row[:n] for r in new_D):
                        new_D.append(new_row)

        D = new_D

    invariants = []
    for row in D:
        inv = row[:n]
        if any(inv):
            invariants.append(inv)
    return invariants


class AnalysisEngine:
    def __init__(self, net):
        self.net = net
        self.unfolded_places = []      # list of (place, color)
        self.unfolded_transitions = [] # list of (transition, color)
        self.Pre = []                  # list of lists
        self.Post = []                 # list of lists
        self.C = []                    # list of lists (Incidence matrix)
        self._unfold()

    def _unfold(self):
        # 1. Unfolded places: sorted by place name, then color name
        places = []
        for p in self.net.places:
            colors = p.colors if p.colors else self.net.colors
            for c in sorted(colors, key=lambda x: x.name):
                places.append((p, c))
        self.unfolded_places = sorted(places, key=lambda x: (x[0].name, x[1].name))

        # 2. Unfolded transitions: sorted by transition name, then color name
        transitions = []
        for t in self.net.transitions:
            colors = t.colors if t.colors else self.net.colors
            for c in sorted(colors, key=lambda x: x.name):
                transitions.append((t, c))
        self.unfolded_transitions = sorted(transitions, key=lambda x: (x[0].name, x[1].name))

        num_places = len(self.unfolded_places)
        num_transitions = len(self.unfolded_transitions)

        # 3. Initialize matrices
        self.Pre = [[0] * num_transitions for _ in range(num_places)]
        self.Post = [[0] * num_transitions for _ in range(num_places)]

        place_idx = {item: idx for idx, item in enumerate(self.unfolded_places)}
        trans_idx = {item: idx for idx, item in enumerate(self.unfolded_transitions)}

        # Fill Pre matrix
        for (t, tc) in self.unfolded_transitions:
            col = trans_idx[(t, tc)]
            for arc in self.net.get_input_arcs(t):
                p = arc.start
                if arc.color_map:
                    for pc, target_multiset in arc.color_map.items():
                        if tc in target_multiset:
                            # Match color by name or identity
                            key = next((k for k in self.unfolded_places if k[0] == p and k[1].name == pc.name), None)
                            if key:
                                row = place_idx[key]
                                self.Pre[row][col] += target_multiset[tc] * arc.weight
                else:
                    key = next((k for k in self.unfolded_places if k[0] == p and k[1].name == tc.name), None)
                    if key:
                        row = place_idx[key]
                        self.Pre[row][col] += arc.weight

        # Fill Post matrix
        for (t, tc) in self.unfolded_transitions:
            col = trans_idx[(t, tc)]
            for arc in self.net.get_output_arcs(t):
                p = arc.end
                if arc.color_map:
                    if tc in arc.color_map:
                        place_multiset = arc.color_map[tc]
                        for pc, count in place_multiset.items():
                            key = next((k for k in self.unfolded_places if k[0] == p and k[1].name == pc.name), None)
                            if key:
                                row = place_idx[key]
                                self.Post[row][col] += count
                else:
                    key = next((k for k in self.unfolded_places if k[0] == p and k[1].name == tc.name), None)
                    if key:
                        row = place_idx[key]
                        self.Post[row][col] += 1

        # 4. Calculate Incidence Matrix C = Post - Pre
        self.C = [[0] * num_transitions for _ in range(num_places)]
        for r in range(num_places):
            for c_idx in range(num_transitions):
                self.C[r][c_idx] = self.Post[r][c_idx] - self.Pre[r][c_idx]

    def get_t_invariants(self):
        return minimal_invariants(self.C)

    def get_p_invariants(self):
        # P-invariants solve C_transpose * y = 0
        C_T = [list(x) for x in zip(*self.C)]
        return minimal_invariants(C_T)

    def compute_coverability_tree(self):
        if not self.unfolded_places:
            return None

        # 1. Initial marking M0
        M0 = {}
        for (p, pc) in self.unfolded_places:
            M0[(p, pc)] = p.get_token_count(pc)

        root = CoverabilityNode(M0)
        queue = [root]

        max_nodes = 500
        node_count = 1

        while queue and node_count < max_nodes:
            curr_node = queue.pop(0)
            curr_marking = curr_node.marking

            # Check if this marking is identical to an ancestor marking
            is_duplicate = False
            ancestor = curr_node.parent
            while ancestor is not None:
                if ancestor.marking == curr_marking:
                    is_duplicate = True
                    break
                ancestor = ancestor.parent
            if is_duplicate:
                continue

            # Try to fire every unfolded transition
            for (t, tc) in self.unfolded_transitions:
                t_idx = self.unfolded_transitions.index((t, tc))

                # Check if enabled
                enabled = True
                for r_idx, (p, pc) in enumerate(self.unfolded_places):
                    req = self.Pre[r_idx][t_idx]
                    if req > 0:
                        if curr_marking[(p, pc)] < req:
                            enabled = False
                            break

                if not enabled:
                    continue

                # Compute next marking
                next_marking = {}
                for r_idx, (p, pc) in enumerate(self.unfolded_places):
                    val = curr_marking[(p, pc)]
                    if val == float('inf'):
                        next_marking[(p, pc)] = float('inf')
                    else:
                        next_marking[(p, pc)] = val - self.Pre[r_idx][t_idx] + self.Post[r_idx][t_idx]

                # Karp-Miller check for ancestors
                ancestor = curr_node.parent
                while ancestor is not None:
                    m_a = ancestor.marking
                    le = True
                    lt = False
                    for (p, pc) in self.unfolded_places:
                        val_a = m_a[(p, pc)]
                        val_next = next_marking[(p, pc)]
                        if val_a > val_next:
                            le = False
                            break
                        if val_a < val_next:
                            lt = True
                    if le and lt:
                        # Introduce infinity for strictly growing places
                        for (p, pc) in self.unfolded_places:
                            if m_a[(p, pc)] < next_marking[(p, pc)]:
                                next_marking[(p, pc)] = float('inf')
                    ancestor = ancestor.parent

                # Create child node
                child = CoverabilityNode(next_marking, parent=curr_node, transition_fired=(t, tc))
                curr_node.children.append(child)
                queue.append(child)
                node_count += 1

        return root

    def format_matrices(self):
        if not self.unfolded_places:
            return "Empty Petri Net."

        res = []
        
        # Header for transitions
        trans_headers = [f"{t.name}({tc.name})" for (t, tc) in self.unfolded_transitions]
        res.append("Places / Transitions:")
        for (p, pc) in self.unfolded_places:
            res.append(f"  P: {p.name}({pc.name})")
        res.append("")
        for (t, tc) in self.unfolded_transitions:
            res.append(f"  T: {t.name}({tc.name})")
        res.append("\n" + "="*50 + "\n")

        def matrix_to_str(name, matrix):
            lines = [f"Matrix {name}:", ""]
            lines.append(" " * 20 + "  ".join(f"{h:>10}" for h in trans_headers))
            for r_idx, (p, pc) in enumerate(self.unfolded_places):
                p_label = f"{p.name}({pc.name})"
                row_vals = "  ".join(f"{matrix[r_idx][c_idx]:>10}" for c_idx in range(len(self.unfolded_transitions)))
                lines.append(f"{p_label:<20} {row_vals}")
            return "\n".join(lines)

        res.append(matrix_to_str("Pre (W-)", self.Pre))
        res.append("\n" + "-"*50 + "\n")
        res.append(matrix_to_str("Post (W+)", self.Post))
        res.append("\n" + "-"*50 + "\n")
        res.append(matrix_to_str("Incidence (C)", self.C))
        return "\n".join(res)

    def format_invariants(self):
        t_invs = self.get_t_invariants()
        p_invs = self.get_p_invariants()

        res = ["=== P-INVARIANTS (Invarianti di Posto) ==="]
        if not p_invs:
            res.append("No non-trivial P-invariants found.")
        else:
            for idx, inv in enumerate(p_invs):
                terms = []
                for val, (p, pc) in zip(inv, self.unfolded_places):
                    if val > 0:
                        terms.append(f"{val}*{p.name}({pc.name})")
                res.append(f"  P-Inv {idx+1}: " + " + ".join(terms) + " = Constant")

        res.append("\n=== T-INVARIANTS (Invarianti di Transizione) ===")
        if not t_invs:
            res.append("No non-trivial T-invariants found.")
        else:
            for idx, inv in enumerate(t_invs):
                terms = []
                for val, (t, tc) in zip(inv, self.unfolded_transitions):
                    if val > 0:
                        terms.append(f"{val}*{t.name}({tc.name})")
                res.append(f"  T-Inv {idx+1}: " + " + ".join(terms) + " = Cycle")

        return "\n".join(res)

    def format_coverability_tree(self):
        root = self.compute_coverability_tree()
        if not root:
            return "Empty Petri Net."

        # 1. Map unique marking vectors to state names: m0, m1, m2...
        marking_labels = {}
        
        def assign_labels(node):
            vec = tuple(node.marking.get(p, 0) for p in self.unfolded_places)
            if vec not in marking_labels:
                idx = len(marking_labels)
                marking_labels[vec] = f"m{idx}"
            for child in node.children:
                assign_labels(child)

        assign_labels(root)

        # 2. Build place header description
        places_header = ", ".join(f"{p.name}({pc.name})" for (p, pc) in self.unfolded_places)
        header_str = f"Places vector order: [{places_header}]\n\n"

        # 3. Recursively build the tree output
        def recurse(node, level=0):
            indent = "  " * level
            vec = tuple(node.marking.get(p, 0) for p in self.unfolded_places)
            label = marking_labels[vec]
            
            vec_str = "[" + ", ".join("inf" if v == float('inf') else str(v) for v in vec) + "]"
            
            fired_str = ""
            if node.transition_fired:
                t, tc = node.transition_fired
                fired_str = f" (Fired: {t.name}({tc.name}))"
            else:
                fired_str = " (Initial Marking)"

            lines = [f"{indent}- {label} = {vec_str}{fired_str}"]
            for child in node.children:
                lines.append(recurse(child, level + 1))
            return "\n".join(lines)

        return "=== COVERABILITY TREE (Albero di Copertura) ===\n\n" + header_str + recurse(root)

