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
            t = t + qdot[k]*qdot[l]*um.cos(q[i]-q[j])
        v = 0.0
        for (i, j) in pairs:
            v = v + um.cos(q[i]) + um.sin(q[j])
        return t - v
    return L


def gc(L, n):
    import os
    import tempfile
    import subprocess
    import ctypes
    import hashlib

    # Op codes
    OP_ADD, OP_SUB, OP_MUL, OP_NEG, OP_SIN, OP_COS, OP_CONST, OP_INPUT = range(8)

    # Graph state
    nodes = []  # List of (op, a, b)
    node_cache = {}  # Map (op, a, b) -> index
    
    # Constant folding helper
    def get_node(op, a, b=None):
        if op == OP_ADD:
            if nodes[a][0] == OP_CONST and nodes[a][1] == 0.0: return b
            if nodes[b][0] == OP_CONST and nodes[b][1] == 0.0: return a
            if nodes[a][0] == OP_CONST and nodes[b][0] == OP_CONST:
                return const_node(nodes[a][1] + nodes[b][1])
        elif op == OP_SUB:
            if nodes[b][0] == OP_CONST and nodes[b][1] == 0.0: return a
            if nodes[a][0] == OP_CONST and nodes[b][0] == OP_CONST:
                return const_node(nodes[a][1] - nodes[b][1])
        elif op == OP_MUL:
            if nodes[a][0] == OP_CONST and nodes[a][1] == 0.0: return const_node(0.0)
            if nodes[b][0] == OP_CONST and nodes[b][1] == 0.0: return const_node(0.0)
            if nodes[a][0] == OP_CONST and nodes[a][1] == 1.0: return b
            if nodes[b][0] == OP_CONST and nodes[b][1] == 1.0: return a
            if nodes[a][0] == OP_CONST and nodes[b][0] == OP_CONST:
                return const_node(nodes[a][1] * nodes[b][1])
        elif op == OP_NEG:
            if nodes[a][0] == OP_CONST: return const_node(-nodes[a][1])
        
        key = (op, a, b)
        if key in node_cache: return node_cache[key]
        idx = len(nodes)
        nodes.append(key)
        node_cache[key] = idx
        return idx

    def const_node(val):
        key = (OP_CONST, val, None)
        if key in node_cache: return node_cache[key]
        idx = len(nodes)
        nodes.append(key)
        node_cache[key] = idx
        return idx

    # Symbolic wrapper
    class Sym:
        def __init__(self, idx): self.idx = idx
        def __add__(self, o): return Sym(get_node(OP_ADD, self.idx, Sym.as_idx(o)))
        def __radd__(self, o): return Sym(get_node(OP_ADD, Sym.as_idx(o), self.idx))
        def __sub__(self, o): return Sym(get_node(OP_SUB, self.idx, Sym.as_idx(o)))
        def __rsub__(self, o): return Sym(get_node(OP_SUB, Sym.as_idx(o), self.idx))
        def __mul__(self, o): return Sym(get_node(OP_MUL, self.idx, Sym.as_idx(o)))
        def __rmul__(self, o): return Sym(get_node(OP_MUL, Sym.as_idx(o), self.idx))
        def __neg__(self): return Sym(get_node(OP_NEG, self.idx, None))
        def __pow__(self, p):
            if p == 2: return self * self
            if p == 1: return self
            if p == 0: return Sym(const_node(1.0))
            raise ValueError("Only power 0, 1, 2 supported")
        @staticmethod
        def as_idx(o): return o.idx if isinstance(o, Sym) else const_node(float(o))

    class UM:
        @staticmethod
        def sin(x): return Sym(get_node(OP_SIN, Sym.as_idx(x), None))
        @staticmethod
        def cos(x): return Sym(get_node(OP_COS, Sym.as_idx(x), None))

    # 1. Trace L
    qs = [Sym(get_node(OP_INPUT, i, None)) for i in range(n)]
    qdots = [Sym(get_node(OP_INPUT, n+i, None)) for i in range(n)]
    L_val = L(qs, qdots, UM())
    
    # 2. Reverse Mode AD to get p = dL/dqdot and f = dL/dq
    grads = {}
    out_idx = Sym.as_idx(L_val)
    grads[out_idx] = const_node(1.0)
    
    def add_grad(i, g):
        if i in grads: grads[i] = get_node(OP_ADD, grads[i], g)
        else: grads[i] = g

    # Iterate strictly over original nodes
    for i in range(len(nodes)-1, -1, -1):
        if i not in grads: continue
        g = grads[i]
        op, a, b = nodes[i]
        
        if op == OP_ADD:
            add_grad(a, g); add_grad(b, g)
        elif op == OP_SUB:
            add_grad(a, g); add_grad(b, get_node(OP_NEG, g, None))
        elif op == OP_MUL:
            add_grad(a, get_node(OP_MUL, g, b)); add_grad(b, get_node(OP_MUL, g, a))
        elif op == OP_NEG:
            add_grad(a, get_node(OP_NEG, g, None))
        elif op == OP_SIN:
            # d(sin u) = cos u * du
            add_grad(a, get_node(OP_MUL, g, get_node(OP_COS, a, None)))
        elif op == OP_COS:
            # d(cos u) = -sin u * du
            s = get_node(OP_NEG, get_node(OP_SIN, a, None), None)
            add_grad(a, get_node(OP_MUL, g, s))

    p = [grads.get(qdots[i].idx, const_node(0.0)) for i in range(n)]
    f = [grads.get(qs[i].idx, const_node(0.0)) for i in range(n)]

    # 3. Symbolic Forward AD for v = (dp/dt)_partial = sum_k (dp/dq_k * qdot_k)
    dot_map = {}
    def get_dot(idx):
        if idx in dot_map: return dot_map[idx]
        op, a, b = nodes[idx]
        res = const_node(0.0)
        
        if op == OP_INPUT:
            if a < n: res = qdots[a].idx # d(q)/dt = qdot
            # d(qdot)/dt is ignored here (part of M term)
        elif op == OP_ADD: res = get_node(OP_ADD, get_dot(a), get_dot(b))
        elif op == OP_SUB: res = get_node(OP_SUB, get_dot(a), get_dot(b))
        elif op == OP_MUL:
            # d(uv) = du*v + u*dv
            res = get_node(OP_ADD, get_node(OP_MUL, get_dot(a), b), get_node(OP_MUL, a, get_dot(b)))
        elif op == OP_NEG: res = get_node(OP_NEG, get_dot(a), None)
        elif op == OP_SIN:
            # d(sin u) = cos u * du
            res = get_node(OP_MUL, get_node(OP_COS, a, None), get_dot(a))
        elif op == OP_COS:
            # d(cos u) = -sin u * du
            res = get_node(OP_MUL, get_node(OP_NEG, get_node(OP_SIN, a, None), None), get_dot(a))
            
        dot_map[idx] = res
        return res

    v_vec = [get_dot(p[i]) for i in range(n)]

    # 4. Symbolic Sparse Forward AD for M = dp/dqdot
    jac_map = {}
    def get_jac(idx):
        if idx in jac_map: return jac_map[idx]
        op, a, b = nodes[idx]
        res = {}
        
        if op == OP_INPUT:
            if a >= n: res[a-n] = const_node(1.0)
        elif op == OP_ADD or op == OP_SUB:
            da, db = get_jac(a), get_jac(b)
            keys = set(da) | set(db)
            for k in keys:
                va, vb = da.get(k, const_node(0.0)), db.get(k, const_node(0.0))
                res[k] = get_node(op, va, vb)
        elif op == OP_MUL:
            da, db = get_jac(a), get_jac(b)
            # Sparsity check
            if da:
                for k, v in da.items():
                    t = get_node(OP_MUL, v, b)
                    res[k] = get_node(OP_ADD, res.get(k, const_node(0.0)), t)
            if db:
                for k, v in db.items():
                    t = get_node(OP_MUL, a, v)
                    res[k] = get_node(OP_ADD, res.get(k, const_node(0.0)), t)
        elif op == OP_NEG:
            da = get_jac(a)
            for k, v in da.items(): res[k] = get_node(OP_NEG, v, None)
        elif op == OP_SIN:
            da = get_jac(a)
            if da:
                c = get_node(OP_COS, a, None)
                for k, v in da.items(): res[k] = get_node(OP_MUL, c, v)
        elif op == OP_COS:
            da = get_jac(a)
            if da:
                s = get_node(OP_NEG, get_node(OP_SIN, a, None), None)
                for k, v in da.items(): res[k] = get_node(OP_MUL, s, v)
        
        jac_map[idx] = res
        return res

    M_entries = []
    for i in range(n):
        row_jac = get_jac(p[i])
        for j, node in row_jac.items():
            if j >= i: # Symmetric
                M_entries.append((i, j, node))

    # 5. Graph compaction
    # Roots: M elements and RHS elements
    rhs_nodes = [get_node(OP_SUB, f[i], v_vec[i]) for i in range(n)]
    roots = [x[2] for x in M_entries] + rhs_nodes
    
    used = set()
    stack = list(roots)
    while stack:
        idx = stack.pop()
        if idx in used: continue
        used.add(idx)
        op, a, b = nodes[idx]
        if op == OP_CONST or op == OP_INPUT: continue
        if a is not None: stack.append(a)
        if b is not None: stack.append(b)
        
    old_to_new = {}
    new_nodes = []
    for idx, item in enumerate(nodes):
        if idx in used:
            old_to_new[idx] = len(new_nodes)
            op, a, b = item
            na = old_to_new.get(a, -1) if a is not None else -1
            nb = old_to_new.get(b, -1) if b is not None else -1
            new_nodes.append((op, na, nb, item))

    # 6. Generate C
    lines = []
    lines.append("#include <math.h>")
    lines.append(f"void cal_opt(double* q, double* qdot, double* qddot) {{")
    lines.append(f"  double w[{len(new_nodes)}];")
    lines.append(f"  double M[{n*n}];")
    lines.append(f"  double rhs[{n}];")
    
    for i, (op, a, b, orig) in enumerate(new_nodes):
        if op == OP_CONST: lines.append(f"  w[{i}] = {orig[1]};")
        elif op == OP_INPUT:
            idx = orig[1]
            if idx < n: lines.append(f"  w[{i}] = q[{idx}];")
            else: lines.append(f"  w[{i}] = qdot[{idx-n}];")
        elif op == OP_ADD: lines.append(f"  w[{i}] = w[{a}] + w[{b}];")
        elif op == OP_SUB: lines.append(f"  w[{i}] = w[{a}] - w[{b}];")
        elif op == OP_MUL: lines.append(f"  w[{i}] = w[{a}] * w[{b}];")
        elif op == OP_NEG: lines.append(f"  w[{i}] = -w[{a}];")
        elif op == OP_SIN: lines.append(f"  w[{i}] = sin(w[{a}]);")
        elif op == OP_COS: lines.append(f"  w[{i}] = cos(w[{a}]);")

    lines.append(f"  for(int i=0;i<{n*n};++i) M[i]=0.0;")
    for r, c, node in M_entries:
        if node in old_to_new:
            idx = old_to_new[node]
            lines.append(f"  M[{r*n+c}] = w[{idx}];")
            if r != c: lines.append(f"  M[{c*n+r}] = w[{idx}];")
            
    for i, node in enumerate(rhs_nodes):
        if node in old_to_new:
            lines.append(f"  rhs[{i}] = w[{old_to_new[node]}];")
        else:
            lines.append(f"  rhs[{i}] = 0.0;")
            
    # LDLt Solver
    lines.append(f"""
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
    lines.append("}")
    
    src = "\n".join(lines)
    
    # Compile
    key = hashlib.md5(src.encode()).hexdigest()
    cdir = os.path.join(tempfile.gettempdir(), "gc_opt_cache")
    os.makedirs(cdir, exist_ok=True)
    so_path = os.path.join(cdir, f"mod_{key}.so")
    
    if not os.path.exists(so_path):
        c_path = os.path.join(cdir, f"src_{key}.c")
        with open(c_path, "w") as f: f.write(src)
        subprocess.check_call(["gcc", "-shared", "-O3", "-march=native", "-fPIC", "-o", so_path, c_path, "-lm"])
        
    lib = ctypes.CDLL(so_path)
    fn = lib.cal_opt
    fn.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    
    def cal_wrapper(q, qd, qdd):
        fn(q.ctypes.data, qd.ctypes.data, qdd.ctypes.data)
        
    return cal_wrapper

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
    L20 = make_synth_L(n, m_terms=40)
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

    print(yl[-1])

    matplotlib.pyplot.plot(yl)
    matplotlib.pyplot.savefig('test.png')


if __name__ == "__main__":
    main()
