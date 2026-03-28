import time

# import autograd
import matplotlib.pyplot
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
            t = t + qdot[i]*qdot[i]
        # coupling terms
        for (i, j), (k, l, _, __) in zip(pairs, quads):
            t = t + qdot[k]*qdot[l]*um.cos(q[i]-q[j])*um.sin(q[i]-q[j])
        v = 0.0
        for (i, j) in pairs:
            v = v + um.cos(q[i]) + um.sin(q[j])
        return t - v
    return L

def gc(L, n):
    """
    继续提速的关键点（只改 gc）：

    1) **把大量 sin/cos( q[i]-q[j] ) 变成“先算每个 q[i] 的 sincos，再用加减公式拼出来”**
       - 这是严格三角恒等式（不是近似），能把每次 cal 中 libm 的 trig 调用数大幅降低。
       - 对于典型 L 里大量 cos(q[i]-q[j]) / sin(q[i]-q[j]) 的情况，收益非常大。

    2) **对同一自变量的 sin/cos 做 sincos 融合**
       - 仍然保留：如果某个表达式既要 sin 又要 cos，则用一次 __builtin_sincos。

    3) **CSE + 常量折叠 + 交换律归一化**
       - 减少生成的节点数（减少 w[] 计算量）。

    返回的 cal(q, qdot, qddot) 与原题接口一致：原地写 qddot。
    """
    import os
    import tempfile
    import subprocess
    import ctypes
    import hashlib
    import math

    # op codes
    OP_ADD, OP_SUB, OP_MUL, OP_NEG, OP_SIN, OP_COS, OP_CONST, OP_INPUT = range(8)

    nodes = []
    node_cache = {}
    const_cache = {}

    def const_node(val: float) -> int:
        if val == 0.0:
            val = 0.0  # normalize -0.0
        idx = const_cache.get(val)
        if idx is not None:
            return idx
        key = (OP_CONST, float(val), -1)
        idx = len(nodes)
        nodes.append(key)
        node_cache[key] = idx
        const_cache[val] = idx
        return idx

    ZERO = const_node(0.0)
    ONE = const_node(1.0)
    NEG_ONE = const_node(-1.0)

    def get_node(op: int, a: int, b: int = -1) -> int:
        # commutative canonicalization
        if op == OP_ADD or op == OP_MUL:
            if a > b:
                a, b = b, a

        # peephole + constant fold
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
            # trig symmetry: sin(-x)=-sin(x), cos(-x)=cos(x)
            if na[0] == OP_NEG:
                inner = na[1]
                if op == OP_SIN:
                    return get_node(OP_NEG, get_node(OP_SIN, inner, -1), -1)
                else:
                    return get_node(OP_COS, inner, -1)
            if na[0] == OP_CONST:
                v = na[1]
                return const_node(math.sin(v) if op == OP_SIN else math.cos(v))

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

    # 1) trace L
    qs = [Sym(get_node(OP_INPUT, i, -1)) for i in range(n)]
    qds = [Sym(get_node(OP_INPUT, n + i, -1)) for i in range(n)]
    out = L(qs, qds, UM())
    out_idx = Sym.as_idx(out)

    # 2) reverse-mode: p=dL/dqdot, f=dL/dq
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
            add_grad(a, g)
            add_grad(b, g)
        elif op == OP_SUB:
            add_grad(a, g)
            add_grad(b, get_node(OP_NEG, g, -1))
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

    # 3) (dp/dt)_partial, ignore qddot part
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

    # 4) sparse Jacobian dp/dqdot
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

    # 5) compact graph to only used nodes
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

    # 6) sin/cos pairing (same operand)
    opnd_sin = {}
    opnd_cos = {}
    for i, (op, na, nb, _) in enumerate(new_nodes):
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

    # 7) detect trig operands of form: 0, ±q[i], ±q[i]±q[j]  (q only, not qdot)
    parse_cache = {}

    def parse_aff(node_i: int):
        if node_i in parse_cache:
            return parse_cache[node_i]
        op, na, nb, orig = new_nodes[node_i]
        res = None
        if op == OP_INPUT:
            k = orig[1]
            if k < n:
                res = [(k, 1)]
        elif op == OP_NEG:
            inner = parse_aff(na)
            if inner is not None:
                res = [(i, -s) for (i, s) in inner]
        elif op == OP_ADD or op == OP_SUB:
            a1 = parse_aff(na)
            b1 = parse_aff(nb)
            if a1 is not None and b1 is not None and len(a1) == 1 and len(b1) == 1:
                (i, sa) = a1[0]
                (j, sb) = b1[0]
                if op == OP_SUB:
                    sb = -sb
                if i == j:
                    s = sa + sb
                    if s == 0:
                        res = []
                    elif abs(s) == 1:
                        res = [(i, s)]
                    else:
                        res = None  # 2*q[i] 不处理（保持走 fallback）
                else:
                    res = [(i, sa), (j, sb)]
        parse_cache[node_i] = res
        return res

    trig_recipe = {}   # operand -> ("ZERO") or ("ONE", i, sign) or ("TWO", i, j, t, g)
    needed_q = set()   # q indices to precompute sincos(q[i])
    for opnd in set(list(opnd_sin.keys()) + list(opnd_cos.keys())):
        aff = parse_aff(opnd)
        if aff is None:
            continue
        if len(aff) == 0:
            trig_recipe[opnd] = ("ZERO",)
        elif len(aff) == 1:
            i, s = aff[0]
            trig_recipe[opnd] = ("ONE", i, s)   # s = ±1
            needed_q.add(i)
        else:
            (i, s1), (j, s2) = aff
            g = 1
            if s1 == -1:
                g = -1
                s2 = -s2
            t = s2  # +1: i+j, -1: i-j
            trig_recipe[opnd] = ("TWO", i, j, t, g)
            needed_q.add(i)
            needed_q.add(j)

    # map M/rhs to compact indices
    M_entries2 = []
    for r, c, node in M_entries:
        wi = old_to_new.get(node)
        if wi is not None:
            M_entries2.append((r, c, wi))
    rhs2 = [old_to_new.get(node, -1) for node in rhs_nodes]

    # 8) C codegen
    c_lines = []
    c_lines.append("#include <math.h>")
    c_lines.append("#include <string.h>")
    c_lines.append("void cal_opt(const double* __restrict q, const double* __restrict qdot, double* __restrict qddot) {")
    c_lines.append(f"  double w[{len(new_nodes)}];")
    c_lines.append(f"  double M[{n*n}];")
    c_lines.append(f"  double rhs[{n}];")

    if needed_q:
        c_lines.append(f"  double sq[{n}];")
        c_lines.append(f"  double cq[{n}];")
        for i in sorted(needed_q):
            c_lines.append(f"  __builtin_sincos(q[{i}], &sq[{i}], &cq[{i}]);")

    for i, (op, a, b, orig) in enumerate(new_nodes):
        if i in pair_first:
            si, ci, opnd = pair_first[i]
            rec = trig_recipe.get(opnd)
            if rec is None:
                c_lines.append(f"  double s{i}, c{i}; __builtin_sincos(w[{opnd}], &s{i}, &c{i});")
                c_lines.append(f"  w[{si}] = s{i}; w[{ci}] = c{i};")
            else:
                if rec[0] == "ZERO":
                    c_lines.append(f"  w[{si}] = 0.0; w[{ci}] = 1.0;")
                elif rec[0] == "ONE":
                    _, qi, sgn = rec
                    if sgn == 1:
                        c_lines.append(f"  w[{si}] = sq[{qi}]; w[{ci}] = cq[{qi}];")
                    else:
                        c_lines.append(f"  w[{si}] = -sq[{qi}]; w[{ci}] = cq[{qi}];")
                else:
                    _, qi, qj, t, g = rec
                    if t == 1:
                        c_lines.append(f"  double s{i} = sq[{qi}]*cq[{qj}] + cq[{qi}]*sq[{qj}];")
                        c_lines.append(f"  double c{i} = cq[{qi}]*cq[{qj}] - sq[{qi}]*sq[{qj}];")
                    else:
                        c_lines.append(f"  double s{i} = sq[{qi}]*cq[{qj}] - cq[{qi}]*sq[{qj}];")
                        c_lines.append(f"  double c{i} = cq[{qi}]*cq[{qj}] + sq[{qi}]*sq[{qj}];")
                    if g == -1:
                        c_lines.append(f"  s{i} = -s{i};")
                    c_lines.append(f"  w[{si}] = s{i}; w[{ci}] = c{i};")
            continue

        if i in skip:
            c_lines.append(f"  /* w[{i}] computed by pair */")
            continue

        if op == OP_CONST:
            c_lines.append(f"  w[{i}] = {orig[1]:.17g};")
        elif op == OP_INPUT:
            k = orig[1]
            if k < n:
                c_lines.append(f"  w[{i}] = q[{k}];")
            else:
                c_lines.append(f"  w[{i}] = qdot[{k-n}];")
        elif op == OP_ADD:
            c_lines.append(f"  w[{i}] = w[{a}] + w[{b}];")
        elif op == OP_SUB:
            c_lines.append(f"  w[{i}] = w[{a}] - w[{b}];")
        elif op == OP_MUL:
            c_lines.append(f"  w[{i}] = w[{a}] * w[{b}];")
        elif op == OP_NEG:
            c_lines.append(f"  w[{i}] = -w[{a}];")
        elif op == OP_SIN or op == OP_COS:
            opnd = a
            rec = trig_recipe.get(opnd)
            if rec is None:
                c_lines.append(f"  w[{i}] = {'sin' if op==OP_SIN else 'cos'}(w[{opnd}]);")
            else:
                if rec[0] == "ZERO":
                    c_lines.append(f"  w[{i}] = {'0.0' if op==OP_SIN else '1.0'};")
                elif rec[0] == "ONE":
                    _, qi, sgn = rec
                    if op == OP_SIN:
                        if sgn == 1:
                            c_lines.append(f"  w[{i}] = sq[{qi}];")
                        else:
                            c_lines.append(f"  w[{i}] = -sq[{qi}];")
                    else:
                        c_lines.append(f"  w[{i}] = cq[{qi}];")
                else:
                    _, qi, qj, t, g = rec
                    if op == OP_SIN:
                        if t == 1:
                            c_lines.append(f"  double s{i} = sq[{qi}]*cq[{qj}] + cq[{qi}]*sq[{qj}];")
                        else:
                            c_lines.append(f"  double s{i} = sq[{qi}]*cq[{qj}] - cq[{qi}]*sq[{qj}];")
                        if g == -1:
                            c_lines.append(f"  s{i} = -s{i};")
                        c_lines.append(f"  w[{i}] = s{i};")
                    else:
                        if t == 1:
                            c_lines.append(f"  w[{i}] = cq[{qi}]*cq[{qj}] - sq[{qi}]*sq[{qj}];")
                        else:
                            c_lines.append(f"  w[{i}] = cq[{qi}]*cq[{qj}] + sq[{qi}]*sq[{qj}];")

    c_lines.append("  memset(M, 0, sizeof(M));")
    for r, c, wi in M_entries2:
        if r >= c:
            c_lines.append(f"  M[{r*n+c}] = w[{wi}];")
        else:
            c_lines.append(f"  M[{c*n+r}] = w[{wi}];")

    for i, wi in enumerate(rhs2):
        if wi == -1:
            c_lines.append(f"  rhs[{i}] = 0.0;")
        else:
            c_lines.append(f"  rhs[{i}] = w[{wi}];")

    # LDL^T solve (no pivot)
    c_lines.append(f"""
  for (int i = 0; i < {n}; i++) {{
    for (int j = 0; j < i; j++) {{
      double sum = M[i * {n} + j];
      for (int k = 0; k < j; k++) sum -= M[i * {n} + k] * M[j * {n} + k] * M[k * {n} + k];
      M[i * {n} + j] = sum / M[j * {n} + j];
    }}
    double sum = M[i * {n} + i];
    for (int k = 0; k < i; k++) {{
      double v = M[i * {n} + k];
      sum -= v * v * M[k * {n} + k];
    }}
    M[i * {n} + i] = sum;
  }}
  for (int i = 0; i < {n}; i++) {{
    double sum = rhs[i];
    for (int k = 0; k < i; k++) sum -= M[i * {n} + k] * rhs[k];
    rhs[i] = sum;
  }}
  for (int i = 0; i < {n}; i++) rhs[i] /= M[i * {n} + i];
  for (int i = {n-1}; i >= 0; i--) {{
    double sum = rhs[i];
    for (int k = i + 1; k < {n}; k++) sum -= M[k * {n} + i] * qddot[k];
    qddot[i] = sum;
  }}
""")
    c_lines.append("}")

    src = "\n".join(c_lines)

    key = hashlib.md5(src.encode("utf-8")).hexdigest()
    cdir = os.path.join(tempfile.gettempdir(), "gc_cache_tri_trig")
    os.makedirs(cdir, exist_ok=True)
    so_path = os.path.join(cdir, f"cal_{key}.so")

    if not os.path.exists(so_path):
        c_path = os.path.join(cdir, f"cal_{key}.c")
        with open(c_path, "w", encoding="utf-8") as f:
            f.write(src)
        subprocess.check_call([
            "gcc", "-shared", "-fPIC",
            "-O3", "-march=native", "-DNDEBUG",
            "-fno-math-errno", "-fno-trapping-math", "-funroll-loops",
            "-o", so_path, c_path, "-lm"
        ])

    lib = ctypes.CDLL(so_path)
    fn = lib.cal_opt
    dblp = ctypes.POINTER(ctypes.c_double)
    fn.argtypes = [dblp, dblp, dblp]
    fn.restype = None

    frombuf = ctypes.c_double.from_buffer

    def cal(q, qdot, qddot):
        fn(frombuf(q), frombuf(qdot), frombuf(qddot))

    return cal


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
    L20 = make_synth_L(n, m_terms=50)
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

    matplotlib.pyplot.plot(yl)
    matplotlib.pyplot.savefig('test.png')


if __name__ == "__main__":
    main()
