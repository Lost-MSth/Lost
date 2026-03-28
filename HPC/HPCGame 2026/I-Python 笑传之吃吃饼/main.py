import time

# import autograd
# import matplotlib.pyplot
import numpy


def make_synth_L(n, m_terms=200):
    # L = sum_i qdot[i]^2 + sum_terms cos(q[i]-q[j]) * qdot[k]*qdot[l] etc
    import random
    import math
    rnd = random.Random(0)
    pairs = [(rnd.randrange(n), rnd.randrange(n)) for _ in range(m_terms)]
    quads = [(rnd.randrange(n), rnd.randrange(n), rnd.randrange(
        n), rnd.randrange(n)) for _ in range(m_terms)]

    def L(q, qdot, um):
        t = 0.0
        # kinetic diagonal
        for i in range(n):
            t = t + qdot[i]*qdot[i]*um.sin(qdot[i])
        # coupling terms
        for (i, j), (k, l, _, __) in zip(pairs, quads):
            t = t + qdot[k]*qdot[l]*um.cos(q[i])*um.sin(-q[j])
        v = 0.0
        for (i, j) in pairs:
            v = v + um.cos(q[i]) + um.sin(q[j])
        return t - v
    return L


def gc(L, n):
    import os, math, hashlib, tempfile, subprocess, sysconfig, importlib.util

    OP_ADD, OP_SUB, OP_MUL, OP_NEG, OP_SIN, OP_COS, OP_CONST, OP_INPUT = range(8)

    nodes = []
    node_cache = {}
    const_cache = {}

    def const_node(v: float) -> int:
        if v == 0.0:
            v = 0.0
        idx = const_cache.get(v)
        if idx is not None:
            return idx
        key = (OP_CONST, float(v), -1)
        idx = len(nodes)
        nodes.append(key)
        node_cache[key] = idx
        const_cache[v] = idx
        return idx

    ZERO = const_node(0.0)
    ONE = const_node(1.0)
    NEG_ONE = const_node(-1.0)

    def get_node(op: int, a: int, b: int = -1) -> int:
        if op == OP_ADD or op == OP_MUL:
            if a > b:
                a, b = b, a

        if op == OP_ADD:
            if a == ZERO:
                return b
            if b == ZERO:
                return a
            na, nb = nodes[a], nodes[b]
            if na[0] == OP_CONST and nb[0] == OP_CONST:
                return const_node(na[1] + nb[1])

        elif op == OP_SUB:
            if b == ZERO:
                return a
            if a == b:
                return ZERO
            na, nb = nodes[a], nodes[b]
            if na[0] == OP_CONST and nb[0] == OP_CONST:
                return const_node(na[1] - nb[1])

        elif op == OP_MUL:
            if a == ZERO or b == ZERO:
                return ZERO
            if a == ONE:
                return b
            if b == ONE:
                return a
            if a == NEG_ONE:
                return get_node(OP_NEG, b, -1)
            if b == NEG_ONE:
                return get_node(OP_NEG, a, -1)
            na, nb = nodes[a], nodes[b]
            if na[0] == OP_CONST and nb[0] == OP_CONST:
                return const_node(na[1] * nb[1])

        elif op == OP_NEG:
            if a == ZERO:
                return ZERO
            na = nodes[a]
            if na[0] == OP_CONST:
                return const_node(-na[1])
            if na[0] == OP_NEG:
                return na[1]

        elif op == OP_SIN or op == OP_COS:
            na = nodes[a]
            if na[0] == OP_NEG:
                inner = na[1]
                if op == OP_SIN:
                    return get_node(OP_NEG, get_node(OP_SIN, inner, -1), -1)
                else:
                    return get_node(OP_COS, inner, -1)
            if na[0] == OP_CONST:
                vv = float(na[1])
                return const_node(math.sin(vv) if op == OP_SIN else math.cos(vv))

        key = (op, a, b)
        idx = node_cache.get(key)
        if idx is not None:
            return idx
        idx = len(nodes)
        nodes.append(key)
        node_cache[key] = idx
        return idx

    class Sym:
        __slots__ = ("idx",)

        def __init__(self, idx: int):
            self.idx = idx

        @staticmethod
        def as_idx(x) -> int:
            return x.idx if isinstance(x, Sym) else const_node(float(x))

        def __add__(self, o): return Sym(get_node(OP_ADD, self.idx, Sym.as_idx(o)))
        def __radd__(self, o): return Sym(get_node(OP_ADD, Sym.as_idx(o), self.idx))
        def __sub__(self, o): return Sym(get_node(OP_SUB, self.idx, Sym.as_idx(o)))
        def __rsub__(self, o): return Sym(get_node(OP_SUB, Sym.as_idx(o), self.idx))
        def __mul__(self, o): return Sym(get_node(OP_MUL, self.idx, Sym.as_idx(o)))
        def __rmul__(self, o): return Sym(get_node(OP_MUL, Sym.as_idx(o), self.idx))
        def __neg__(self): return Sym(get_node(OP_NEG, self.idx, -1))

        def __pow__(self, p: int):
            if p == 2:
                return self * self
            if p == 1:
                return self
            if p == 0:
                return Sym(ONE)
            raise ValueError("Only **0/**1/**2 supported")

    class UM:
        @staticmethod
        def sin(x): return Sym(get_node(OP_SIN, Sym.as_idx(x), -1))

        @staticmethod
        def cos(x): return Sym(get_node(OP_COS, Sym.as_idx(x), -1))

    # ---- trace L ----
    qs = [Sym(get_node(OP_INPUT, i, -1)) for i in range(n)]
    qds = [Sym(get_node(OP_INPUT, n + i, -1)) for i in range(n)]
    out = L(qs, qds, UM())
    out_idx = Sym.as_idx(out)

    # ---- reverse mode ----
    grads = {out_idx: ONE}

    def add_grad(i: int, g: int):
        prev = grads.get(i)
        grads[i] = g if prev is None else get_node(OP_ADD, prev, g)

    for i in range(len(nodes) - 1, -1, -1):
        g = grads.get(i)
        if g is None:
            continue
        op, a, b = nodes[i]
        if op == OP_ADD:
            add_grad(a, g); add_grad(b, g)
        elif op == OP_SUB:
            add_grad(a, g); add_grad(b, get_node(OP_NEG, g, -1))
        elif op == OP_MUL:
            add_grad(a, get_node(OP_MUL, g, b))
            add_grad(b, get_node(OP_MUL, g, a))
        elif op == OP_NEG:
            add_grad(a, get_node(OP_NEG, g, -1))
        elif op == OP_SIN:
            add_grad(a, get_node(OP_MUL, g, get_node(OP_COS, a, -1)))
        elif op == OP_COS:
            add_grad(a, get_node(OP_MUL, g, get_node(OP_NEG, get_node(OP_SIN, a, -1), -1)))

    p = [grads.get(qds[i].idx, ZERO) for i in range(n)]
    f = [grads.get(qs[i].idx, ZERO) for i in range(n)]

    # ---- partial time derivative (ignore qddot) ----
    dot_cache = {}

    def get_dot(idx: int) -> int:
        v = dot_cache.get(idx)
        if v is not None:
            return v
        op, a, b = nodes[idx]
        if op == OP_INPUT:
            res = qds[a].idx if a < n else ZERO
        elif op == OP_ADD:
            res = get_node(OP_ADD, get_dot(a), get_dot(b))
        elif op == OP_SUB:
            res = get_node(OP_SUB, get_dot(a), get_dot(b))
        elif op == OP_MUL:
            res = get_node(OP_ADD,
                           get_node(OP_MUL, get_dot(a), b),
                           get_node(OP_MUL, a, get_dot(b)))
        elif op == OP_NEG:
            res = get_node(OP_NEG, get_dot(a), -1)
        elif op == OP_SIN:
            res = get_node(OP_MUL, get_node(OP_COS, a, -1), get_dot(a))
        elif op == OP_COS:
            res = get_node(OP_MUL, get_node(OP_NEG, get_node(OP_SIN, a, -1), -1), get_dot(a))
        else:
            res = ZERO
        dot_cache[idx] = res
        return res

    v = [get_dot(pi) for pi in p]

    # ---- sparse Jacobian dp/dqdot ----
    jac_cache = {}

    def get_jac(idx: int):
        cached = jac_cache.get(idx)
        if cached is not None:
            return cached
        op, a, b = nodes[idx]
        if op == OP_INPUT:
            res = {a - n: ONE} if a >= n else {}
        elif op == OP_ADD or op == OP_SUB:
            da, db = get_jac(a), get_jac(b)
            if not da and not db:
                res = {}
            else:
                keys = set(da) | set(db)
                res = {k: get_node(op, da.get(k, ZERO), db.get(k, ZERO)) for k in keys}
        elif op == OP_MUL:
            da, db = get_jac(a), get_jac(b)
            res = {}
            if da:
                for k, vv in da.items():
                    res[k] = get_node(OP_ADD, res.get(k, ZERO), get_node(OP_MUL, vv, b))
            if db:
                for k, vv in db.items():
                    res[k] = get_node(OP_ADD, res.get(k, ZERO), get_node(OP_MUL, a, vv))
        elif op == OP_NEG:
            da = get_jac(a)
            res = {k: get_node(OP_NEG, vv, -1) for k, vv in da.items()} if da else {}
        elif op == OP_SIN:
            da = get_jac(a)
            if da:
                c = get_node(OP_COS, a, -1)
                res = {k: get_node(OP_MUL, c, vv) for k, vv in da.items()}
            else:
                res = {}
        elif op == OP_COS:
            da = get_jac(a)
            if da:
                s = get_node(OP_NEG, get_node(OP_SIN, a, -1), -1)
                res = {k: get_node(OP_MUL, s, vv) for k, vv in da.items()}
            else:
                res = {}
        else:
            res = {}
        jac_cache[idx] = res
        return res

    M_entries = []
    for i in range(n):
        row = get_jac(p[i])
        for j, node_idx in row.items():
            if j >= i:
                M_entries.append((i, j, node_idx))

    rhs_nodes = [get_node(OP_SUB, f[i], v[i]) for i in range(n)]

    # ---- compact used nodes ----
    roots = [node for _, _, node in M_entries] + rhs_nodes
    used = set()
    stack = roots[:]
    while stack:
        idx = stack.pop()
        if idx in used:
            continue
        used.add(idx)
        op, a, b = nodes[idx]
        if op == OP_CONST or op == OP_INPUT:
            continue
        if a != -1:
            stack.append(a)
        if b != -1:
            stack.append(b)

    old_to_new = {}
    new_nodes = []
    for idx, item in enumerate(nodes):
        if idx in used:
            old_to_new[idx] = len(new_nodes)
            op, a, b = item
            na = old_to_new.get(a, -1) if a != -1 else -1
            nb = old_to_new.get(b, -1) if b != -1 else -1
            new_nodes.append((op, na, nb, item))

    # ---- sin/cos pairing ----
    opnd_sin = {}
    opnd_cos = {}
    for i, (op, na, _, _) in enumerate(new_nodes):
        if op == OP_SIN:
            opnd_sin[na] = i
        elif op == OP_COS:
            opnd_cos[na] = i

    pair_first = {}
    skip = set()
    for opnd, si in opnd_sin.items():
        ci = opnd_cos.get(opnd)
        if ci is None:
            continue
        first = si if si < ci else ci
        pair_first[first] = (si, ci, opnd)
        skip.add(ci if si < ci else si)

    # ---- parse affine for trig reuse: <=2 inputs (q/qdot) coeff ±1 + const ----
    parse_cache = {}

    def _valid_terms(terms):
        items = [(k, v) for k, v in terms.items() if v != 0]
        if len(items) > 2:
            return None
        for _, v in items:
            if v not in (-1, 1):
                return None
        return dict(items)

    def parse_aff(node_i: int):
        cached = parse_cache.get(node_i)
        if cached is not None:
            return cached
        op, na, nb, orig = new_nodes[node_i]
        res = None
        if op == OP_CONST:
            res = ({}, float(orig[1]))
        elif op == OP_INPUT:
            k = int(orig[1])
            if 0 <= k < 2 * n:
                res = ({k: 1}, 0.0)
        elif op == OP_NEG:
            inner = parse_aff(na)
            if inner is not None:
                t, c = inner
                res = ({k: -v for k, v in t.items()}, -c)
        elif op == OP_ADD or op == OP_SUB:
            a1 = parse_aff(na)
            b1 = parse_aff(nb)
            if a1 is not None and b1 is not None:
                ta, ca = a1
                tb, cb = b1
                if op == OP_SUB:
                    tb = {k: -v for k, v in tb.items()}
                    cb = -cb
                terms = dict(ta)
                for k, vv in tb.items():
                    terms[k] = terms.get(k, 0) + vv
                terms = _valid_terms(terms)
                if terms is not None:
                    cst = ca + cb
                    if cst == 0.0:
                        cst = 0.0
                    res = (terms, float(cst))
        parse_cache[node_i] = res
        return res

    trig_recipe = {}
    needed_q = set()
    needed_qd = set()

    def mark_needed(inp_idx: int):
        if inp_idx < n:
            needed_q.add(inp_idx)
        else:
            needed_qd.add(inp_idx - n)

    for opnd in set(opnd_sin.keys()) | set(opnd_cos.keys()):
        aff = parse_aff(opnd)
        if aff is None:
            continue
        terms, cst = aff
        if not terms:
            if cst == 0.0:
                trig_recipe[opnd] = ("ZERO",)
            else:
                trig_recipe[opnd] = ("CONST", float(cst))
            continue
        items = list(terms.items())
        if len(items) == 1:
            k, sgn = items[0]
            trig_recipe[opnd] = ("ONE", int(k), int(sgn), float(cst))
            mark_needed(int(k))
        else:
            (k1, s1), (k2, s2) = items[0], items[1]
            g = 1
            if s1 == -1:
                g = -1
                s2 = -s2
            t = int(s2)
            trig_recipe[opnd] = ("TWO", int(k1), int(k2), t, g, float(cst))
            mark_needed(int(k1)); mark_needed(int(k2))

    # ---- map M/rhs nodes into compact graph indices ----
    M_entries2 = []
    for r, c, node in M_entries:
        wi = old_to_new.get(node)
        if wi is not None:
            M_entries2.append((r, c, wi))
    rhs2 = [old_to_new.get(node, -1) for node in rhs_nodes]

    # ---- build adjacency pattern of M (old index) ----
    if n <= 30:
        adj0 = [0] * n
        for r, c, _wi in M_entries2:
            if r == c:
                continue
            adj0[r] |= (1 << c)
            adj0[c] |= (1 << r)

        try:
            _bit_count = int.bit_count  # py>=3.8
            def popcnt(x) -> int:
                return _bit_count(int(x))
        except Exception:
            def popcnt(x) -> int:
                return bin(int(x)).count("1")

        # min-degree (very small n=20 => enough)
        rem = (1 << n) - 1
        perm = []
        adjw = adj0[:]  # mutated
        for _ in range(n):
            best_v = -1
            best_deg = 10**9
            m = rem
            while m:
                v = (m & -m).bit_length() - 1
                m &= m - 1
                deg = popcnt(adjw[v] & rem)
                if deg < best_deg:
                    best_deg = deg
                    best_v = v
            v = best_v
            perm.append(v)
            neigh = adjw[v] & (rem ^ (1 << v))
            # add fill clique among neigh
            mm = neigh
            while mm:
                u = (mm & -mm).bit_length() - 1
                mm &= mm - 1
                adjw[u] |= (neigh ^ (1 << u))
            # remove v
            mm = neigh
            while mm:
                u = (mm & -mm).bit_length() - 1
                mm &= mm - 1
                adjw[u] &= ~(1 << v)
            adjw[v] = 0
            rem &= ~(1 << v)

        invperm = [0] * n
        for new_i, old_i in enumerate(perm):
            invperm[old_i] = new_i

        # permute adjacency
        adjP = [0] * n
        for old_i in range(n):
            ni = invperm[old_i]
            bits = adj0[old_i]
            nb = 0
            while bits:
                j = (bits & -bits).bit_length() - 1
                bits &= bits - 1
                nb |= (1 << invperm[j])
            adjP[ni] = nb

        # chordal completion in permuted order => fullP
        fullP = adjP[:]
        cur = adjP[:]
        for j in range(n):
            higher = cur[j] & ~((1 << (j + 1)) - 1)
            mm = higher
            while mm:
                u = (mm & -mm).bit_length() - 1
                mm &= mm - 1
                add = higher & ~(1 << u)
                cur[u] |= add
                fullP[u] |= add
            # also update fullP[j] with higher (not necessary for rowmask<j)
            # remove j from higher neighbors
            mm = higher
            while mm:
                u = (mm & -mm).bit_length() - 1
                mm &= mm - 1
                cur[u] &= ~(1 << j)
            cur[j] = 0

        rowmask = [0] * n
        for i in range(n):
            rowmask[i] = fullP[i] & ((1 << i) - 1)

        colmask = [0] * n
        for i in range(n):
            m = rowmask[i]
            while m:
                j = (m & -m).bit_length() - 1
                m &= m - 1
                colmask[j] |= (1 << i)
    else:
        perm = list(range(n))
        invperm = list(range(n))
        rowmask = [((1 << i) - 1) for i in range(n)]
        colmask = [0] * n
        for i in range(n):
            colmask[i] = (~((1 << (i + 1)) - 1)) & ((1 << n) - 1)

    def c_lit(x: float) -> str:
        if x == 0.0:
            x = 0.0
        return f"{x:.17g}"

    def var_s(k: int) -> str:
        return f"sq[{k}]" if k < n else f"sqd[{k-n}]"

    def var_c(k: int) -> str:
        return f"cq[{k}]" if k < n else f"cqd[{k-n}]"

    def emit_sincos(opnd: int, sname: str, cname: str, tag: str):
        rec = trig_recipe.get(opnd)
        Ls = []
        if rec is None:
            Ls.append(f"  __builtin_sincos(w[{opnd}], &{sname}, &{cname});")
            return Ls
        if rec[0] == "ZERO":
            Ls.append(f"  {sname} = 0.0; {cname} = 1.0;")
            return Ls
        if rec[0] == "CONST":
            cst = float(rec[1])
            Ls.append(f"  {sname} = {c_lit(math.sin(cst))}; {cname} = {c_lit(math.cos(cst))};")
            return Ls

        sb = f"sb_{tag}"
        cb = f"cb_{tag}"

        if rec[0] == "ONE":
            _, k, sgn, cst = rec
            if sgn == 1:
                Ls.append(f"  double {sb} = {var_s(k)};")
                Ls.append(f"  double {cb} = {var_c(k)};")
            else:
                Ls.append(f"  double {sb} = -({var_s(k)});")
                Ls.append(f"  double {cb} = {var_c(k)};")
            if cst == 0.0:
                Ls.append(f"  {sname} = {sb}; {cname} = {cb};")
                return Ls
            sc = math.sin(cst); cc = math.cos(cst)
            Ls.append(f"  {sname} = {sb}*{c_lit(cc)} + {cb}*{c_lit(sc)};")
            Ls.append(f"  {cname} = {cb}*{c_lit(cc)} - {sb}*{c_lit(sc)};")
            return Ls

        _, k1, k2, t, g, cst = rec
        s1 = f"s1_{tag}"; c1 = f"c1_{tag}"
        s2 = f"s2_{tag}"; c2 = f"c2_{tag}"

        Ls.append(f"  double {s1} = {var_s(k1)};")
        Ls.append(f"  double {c1} = {var_c(k1)};")
        Ls.append(f"  double {s2} = {var_s(k2)};")
        Ls.append(f"  double {c2} = {var_c(k2)};")

        if t == 1:
            Ls.append(f"  double {sb} = {s1}*{c2} + {c1}*{s2};")
            Ls.append(f"  double {cb} = {c1}*{c2} - {s1}*{s2};")
        else:
            Ls.append(f"  double {sb} = {s1}*{c2} - {c1}*{s2};")
            Ls.append(f"  double {cb} = {c1}*{c2} + {s1}*{s2};")
        if g == -1:
            Ls.append(f"  {sb} = -{sb};")
        if cst == 0.0:
            Ls.append(f"  {sname} = {sb}; {cname} = {cb};")
            return Ls
        sc = math.sin(cst); cc = math.cos(cst)
        Ls.append(f"  {sname} = {sb}*{c_lit(cc)} + {cb}*{c_lit(sc)};")
        Ls.append(f"  {cname} = {cb}*{c_lit(cc)} - {sb}*{c_lit(sc)};")
        return Ls

    # ---- C extension codegen ----
    cal_lines = []
    cal_lines.append("#define PY_SSIZE_T_CLEAN")
    cal_lines.append("#include <Python.h>")
    cal_lines.append("#include <math.h>")
    cal_lines.append("#include <string.h>")
    cal_lines.append("#include <stdint.h>")
    cal_lines.append("")

    cal_lines.append(f"static inline void cal_opt(const double* __restrict q, const double* __restrict qdot, double* __restrict qddot) {{")
    cal_lines.append(f"  double w[{len(new_nodes)}];")
    cal_lines.append(f"  double M[{n*n}];")
    cal_lines.append(f"  double rhs[{n}];")
    cal_lines.append(f"  double sol[{n}];")
    cal_lines.append(f"  double invD[{n}];")

    if needed_q:
        cal_lines.append(f"  double sq[{n}], cq[{n}];")
        for i in sorted(needed_q):
            cal_lines.append(f"  __builtin_sincos(q[{i}], &sq[{i}], &cq[{i}]);")
    if needed_qd:
        cal_lines.append(f"  double sqd[{n}], cqd[{n}];")
        for i in sorted(needed_qd):
            cal_lines.append(f"  __builtin_sincos(qdot[{i}], &sqd[{i}], &cqd[{i}]);")

    # compute w graph
    for i, (op, a, b, orig) in enumerate(new_nodes):
        if i in pair_first:
            si, ci, opnd = pair_first[i]
            sname = f"s{i}"
            cname = f"c{i}"
            cal_lines.append(f"  double {sname}, {cname};")
            cal_lines.extend(emit_sincos(opnd, sname, cname, f"pair_{i}"))
            cal_lines.append(f"  w[{si}] = {sname}; w[{ci}] = {cname};")
            continue
        if i in skip:
            cal_lines.append(f"  /* w[{i}] computed by pair */")
            continue
        if op == OP_CONST:
            cal_lines.append(f"  w[{i}] = {c_lit(float(orig[1]))};")
        elif op == OP_INPUT:
            k = int(orig[1])
            if k < n:
                cal_lines.append(f"  w[{i}] = q[{k}];")
            else:
                cal_lines.append(f"  w[{i}] = qdot[{k-n}];")
        elif op == OP_ADD:
            cal_lines.append(f"  w[{i}] = w[{a}] + w[{b}];")
        elif op == OP_SUB:
            cal_lines.append(f"  w[{i}] = w[{a}] - w[{b}];")
        elif op == OP_MUL:
            cal_lines.append(f"  w[{i}] = w[{a}] * w[{b}];")
        elif op == OP_NEG:
            cal_lines.append(f"  w[{i}] = -w[{a}];")
        elif op == OP_SIN or op == OP_COS:
            opnd = a
            rec = trig_recipe.get(opnd)
            if rec is None:
                cal_lines.append(f"  w[{i}] = {'sin' if op==OP_SIN else 'cos'}(w[{opnd}]);")
            else:
                sname = f"ss{i}"
                cname = f"cc{i}"
                cal_lines.append(f"  double {sname}, {cname};")
                cal_lines.extend(emit_sincos(opnd, sname, cname, f"trig_{i}"))
                cal_lines.append(f"  w[{i}] = {(sname if op==OP_SIN else cname)};")
        else:
            cal_lines.append(f"  w[{i}] = 0.0;")

    # constants for permutation + masks
    cal_lines.append("")
    cal_lines.append(f"  static const int perm[{n}] = {{{', '.join(str(x) for x in perm)}}};")
    cal_lines.append(f"  static const int invperm[{n}] = {{{', '.join(str(x) for x in invperm)}}};")
    cal_lines.append(f"  static const uint32_t rowmask[{n}] = {{{', '.join(str(int(x)) for x in rowmask)}}};")
    cal_lines.append(f"  static const uint32_t colmask[{n}] = {{{', '.join(str(int(x)) for x in colmask)}}};")
    cal_lines.append("")

    # build permuted A in lower triangle only
    cal_lines.append("  memset(M, 0, sizeof(M));")
    # fill diagonal default 0 already
    for r, c, wi in M_entries2:
        pr = invperm[r]
        pc = invperm[c]
        if pr == pc:
            cal_lines.append(f"  M[{pr}*{n}+{pr}] = w[{wi}];")
        else:
            # store in lower: i>j
            if pr > pc:
                cal_lines.append(f"  M[{pr}*{n}+{pc}] = w[{wi}];")
            else:
                cal_lines.append(f"  M[{pc}*{n}+{pr}] = w[{wi}];")

    # rhs permute
    for old_i, wi in enumerate(rhs2):
        pi = invperm[old_i]
        if wi == -1:
            cal_lines.append(f"  rhs[{pi}] = 0.0;")
        else:
            cal_lines.append(f"  rhs[{pi}] = w[{wi}];")

    # ---- sparse LDL^T via bitmask; invD reduces divisions ----
    cal_lines.append(f"""
  for (int i = 0; i < {n}; i++) {{
    uint32_t mi = rowmask[i];
    while (mi) {{
      uint32_t lsb = mi & (uint32_t)(- (int32_t)mi);
      int j = __builtin_ctz(mi);
      mi ^= lsb;

      double sum = M[i*{n} + j];  /* A_ij (possibly 0 for fill edge) */
      uint32_t inter = rowmask[i] & rowmask[j] & ((j==0) ? 0u : ((1u << j) - 1u));
      while (inter) {{
        uint32_t lsb2 = inter & (uint32_t)(- (int32_t)inter);
        int k = __builtin_ctz(inter);
        inter ^= lsb2;
        sum -= M[i*{n} + k] * M[j*{n} + k] * M[k*{n} + k];
      }}
      /* L_ij = sum / D_j ; use invD[j] (already set because D_j computed at end of row j) */
      M[i*{n} + j] = sum * invD[j];
    }}

    double dsum = M[i*{n} + i];  /* A_ii */
    uint32_t mk = rowmask[i];
    while (mk) {{
      uint32_t lsb3 = mk & (uint32_t)(- (int32_t)mk);
      int k = __builtin_ctz(mk);
      mk ^= lsb3;
      double v = M[i*{n} + k];
      dsum -= v * v * M[k*{n} + k];
    }}
    M[i*{n} + i] = dsum;
    invD[i] = 1.0 / dsum;
  }}

  /* forward: solve L z = rhs (in-place rhs) */
  for (int i = 0; i < {n}; i++) {{
    double sum = rhs[i];
    uint32_t mk = rowmask[i];
    while (mk) {{
      uint32_t lsb3 = mk & (uint32_t)(- (int32_t)mk);
      int k = __builtin_ctz(mk);
      mk ^= lsb3;
      sum -= M[i*{n} + k] * rhs[k];
    }}
    rhs[i] = sum;
  }}

  /* D^{-1} */
  for (int i = 0; i < {n}; i++) rhs[i] *= invD[i];

  /* backward: solve L^T x = rhs => sol */
  for (int i = {n}-1; i >= 0; i--) {{
    double sum = rhs[i];
    uint32_t mk = colmask[i] & ~((1u << (i+1)) - 1u);  /* rows > i where L(row,i) exists */
    while (mk) {{
      uint32_t lsb3 = mk & (uint32_t)(- (int32_t)mk);
      int r = __builtin_ctz(mk);
      mk ^= lsb3;
      sum -= M[r*{n} + i] * sol[r];
    }}
    sol[i] = sum;
  }}

  /* scatter back to original order */
  for (int i = 0; i < {n}; i++) {{
    qddot[ perm[i] ] = sol[i];
  }}
}}""")

    # Python wrapper
    cal_lines.append(r"""
static PyObject* py_cal(PyObject* self, PyObject* args){
  PyObject *oq,*oqd,*oqdd;
  if(!PyArg_ParseTuple(args,"OOO",&oq,&oqd,&oqdd)) return NULL;
  Py_buffer bq={0},bqd={0},bqdd={0};
  if(PyObject_GetBuffer(oq,&bq,PyBUF_CONTIG_RO|PyBUF_FORMAT)<0) return NULL;
  if(PyObject_GetBuffer(oqd,&bqd,PyBUF_CONTIG_RO|PyBUF_FORMAT)<0){ PyBuffer_Release(&bq); return NULL; }
  if(PyObject_GetBuffer(oqdd,&bqdd,PyBUF_CONTIG|PyBUF_FORMAT|PyBUF_WRITABLE)<0){ PyBuffer_Release(&bqd); PyBuffer_Release(&bq); return NULL; }

  int ok=1;
  if(bq.itemsize!=8||bqd.itemsize!=8||bqdd.itemsize!=8) ok=0;
  if(!bq.format||!bqd.format||!bqdd.format) ok=0;
  if(ok && !(bq.format[0]=='d' && bq.format[1]=='\0')) ok=0;
  if(ok && !(bqd.format[0]=='d' && bqd.format[1]=='\0')) ok=0;
  if(ok && !(bqdd.format[0]=='d' && bqdd.format[1]=='\0')) ok=0;
""")
    cal_lines.append(f"  if(ok){{ if(bq.len<(Py_ssize_t)({n}*8)||bqd.len<(Py_ssize_t)({n}*8)||bqdd.len<(Py_ssize_t)({n}*8)) ok=0; }}")
    cal_lines.append(r"""
  if(!ok){
    PyBuffer_Release(&bqdd); PyBuffer_Release(&bqd); PyBuffer_Release(&bq);
    PyErr_SetString(PyExc_TypeError,"q/qdot/qddot must be contiguous float64 buffers, len>=n");
    return NULL;
  }

  cal_opt((const double*)bq.buf,(const double*)bqd.buf,(double*)bqdd.buf);

  PyBuffer_Release(&bqdd); PyBuffer_Release(&bqd); PyBuffer_Release(&bq);
  Py_RETURN_NONE;
}

static PyMethodDef Methods[] = {
  {"cal", (PyCFunction)py_cal, METH_VARARGS, NULL},
  {NULL, NULL, 0, NULL}
};
""")

    src_core = "\n".join(cal_lines)
    key = hashlib.md5(src_core.encode("utf-8")).hexdigest()
    modname = f"calmod_{key}"

    # append module def with correct name (string literal!)
    src = src_core + f'\nstatic struct PyModuleDef Module = {{ PyModuleDef_HEAD_INIT, "{modname}", NULL, -1, Methods }};\n' \
                     f'PyMODINIT_FUNC PyInit_{modname}(void) {{ return PyModule_Create(&Module); }}\n'

    # build & load extension
    cdir = os.path.join(tempfile.gettempdir(), "gc_cache_ext_fast_sparse")
    os.makedirs(cdir, exist_ok=True)
    ext_suffix = sysconfig.get_config_var("EXT_SUFFIX") or ".so"
    so_path = os.path.join(cdir, f"{modname}{ext_suffix}")
    c_path = os.path.join(cdir, f"{modname}.c")

    if not os.path.exists(so_path):
        with open(c_path, "w", encoding="utf-8") as f:
            f.write(src)
        include_py = sysconfig.get_config_var("INCLUDEPY") or ""
        cc = os.environ.get("CC", "gcc")
        cmd = [
            cc, "-shared", "-fPIC",
            "-Ofast", "-march=native", "-DNDEBUG",
            "-fno-math-errno", "-fno-trapping-math",
            "-ffp-contract=fast", "-fomit-frame-pointer",
            "-funroll-loops", "-pipe",
            f"-I{include_py}",
            "-o", so_path, c_path, "-lm",
        ]
        try:
            subprocess.check_call(cmd)
        except Exception:
            libdir = sysconfig.get_config_var("LIBDIR") or ""
            ldl = sysconfig.get_config_var("LDLIBRARY") or ""
            extra = []
            if libdir:
                extra += [f"-L{libdir}"]
            if ldl.startswith("lib") and (".so" in ldl or ".a" in ldl):
                extra += [f"-l{ldl[3:].split('.')[0]}"]
            subprocess.check_call(cmd + extra)

    spec = importlib.util.spec_from_file_location(modname, so_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.cal




def check(a, b):
    def l(q, qdot, usermath):
        t = 0.0
        t = t+qdot[0]*qdot[0]
        t = t+qdot[1]*qdot[1]+qdot[0]*qdot[0] + \
            qdot[0]*qdot[1]*2.0*usermath.cos(q[0]-q[1])
        v = -2*usermath.cos(q[0])-usermath.cos(q[1])
        return t-v
    n = 2
    cal = gc(l, n)

    q = numpy.zeros(n, dtype=numpy.float64)
    qdot = numpy.zeros(n, dtype=numpy.float64)
    k1 = numpy.zeros(n, dtype=numpy.float64)

    q[0] = a
    qdot[0] = b

    dt = 0.02
    recn = 100

    r = numpy.zeros((recn, n), dtype=numpy.float64)

    start = time.time()
    for i in range(recn):
        for j in range(10):
            cal(q, qdot, k1)

            qdot_ = qdot+0.5*dt*k1
            q_ = q+0.5*dt*qdot_
            cal(q_, qdot_, k1)

            qdot_ = qdot+0.5*dt*k1
            q_ = q+0.5*dt*qdot_
            cal(q_, qdot_, k1)

            qdot_ = qdot+dt*k1
            q = q+0.5*dt*(qdot_+qdot)
            qdot = qdot_
        r[i] = q
    end = time.time()
    print("Time:", end - start)
    return r


def test_speed(a, b):
    n = 20
    L20 = make_synth_L(n, m_terms=500)
    cal = gc(L20, n)

    q = numpy.zeros(n, dtype=numpy.float64)
    qdot = numpy.zeros(n, dtype=numpy.float64)
    k1 = numpy.zeros(n, dtype=numpy.float64)

    q[0] = a
    qdot[0] = b

    dt = 0.02
    recn = 5000

    r = numpy.zeros((recn, n), dtype=numpy.float64)

    start = time.time()
    for i in range(recn):
        for j in range(10):
            cal(q, qdot, k1)

            qdot_ = qdot+0.5*dt*k1
            q_ = q+0.5*dt*qdot_
            cal(q_, qdot_, k1)

            qdot_ = qdot+0.5*dt*k1
            q_ = q+0.5*dt*qdot_
            cal(q_, qdot_, k1)

            qdot_ = qdot+dt*k1
            q = q+0.5*dt*(qdot_+qdot)
            qdot = qdot_
        r[i] = q
    end = time.time()
    print("Time:", end - start)
    return r


def main():

    yl = check(0, 0.7)
    test_speed(0, 0.7)
    numpy.set_printoptions(precision=32)

    print(yl[-1])

    #matplotlib.pyplot.plot(yl)
    #matplotlib.pyplot.savefig('test.png')


if __name__ == "__main__":
    main()
