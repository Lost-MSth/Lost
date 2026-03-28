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
    flags=["-O3", "-march=native"]
    import os, tempfile, subprocess, ctypes, hashlib, math
    OP_ADD, OP_SUB, OP_MUL, OP_NEG, OP_SIN, OP_COS, OP_CONST, OP_INPUT = range(8)
    nodes=[]; node_cache={}; const_cache={}
    def const_node(val):
        if val==0.0: val=0.0
        if val in const_cache: return const_cache[val]
        key=(OP_CONST,val,-1); idx=len(nodes); nodes.append(key); const_cache[val]=idx; node_cache[key]=idx; return idx
    ZERO=const_node(0.0); ONE=const_node(1.0); NEG_ONE=const_node(-1.0)
    def get_node(op,a,b=-1):
        if op==OP_ADD or op==OP_MUL:
            if a>b: a,b=b,a
        if op==OP_ADD:
            if a==ZERO: return b
            if b==ZERO: return a
            if nodes[a][0]==OP_NEG and nodes[a][1]==b: return ZERO
            if nodes[b][0]==OP_NEG and nodes[b][1]==a: return ZERO
            if nodes[a][0]==OP_CONST and nodes[b][0]==OP_CONST:
                return const_node(nodes[a][1]+nodes[b][1])
        elif op==OP_SUB:
            if b==ZERO: return a
            if a==b: return ZERO
            if nodes[a][0]==OP_CONST and nodes[b][0]==OP_CONST:
                return const_node(nodes[a][1]-nodes[b][1])
        elif op==OP_MUL:
            if a==ZERO or b==ZERO: return ZERO
            if a==ONE: return b
            if b==ONE: return a
            if a==NEG_ONE: return get_node(OP_NEG,b,-1)
            if b==NEG_ONE: return get_node(OP_NEG,a,-1)
            if nodes[a][0]==OP_CONST and nodes[b][0]==OP_CONST:
                return const_node(nodes[a][1]*nodes[b][1])
        elif op==OP_NEG:
            if a==ZERO: return ZERO
            if nodes[a][0]==OP_CONST: return const_node(-nodes[a][1])
            if nodes[a][0]==OP_NEG: return nodes[a][1]
        elif op==OP_SIN or op==OP_COS:
            if nodes[a][0]==OP_CONST:
                v=nodes[a][1]
                return const_node(math.sin(v) if op==OP_SIN else math.cos(v))
        key=(op,a,b)
        if key in node_cache: return node_cache[key]
        idx=len(nodes); nodes.append(key); node_cache[key]=idx; return idx
    class Sym:
        __slots__=("idx",)
        def __init__(self, idx): self.idx=idx
        @staticmethod
        def as_idx(o):
            if isinstance(o, Sym): return o.idx
            return const_node(float(o))
        def __add__(self,o): return Sym(get_node(OP_ADD,self.idx,Sym.as_idx(o)))
        def __radd__(self,o): return Sym(get_node(OP_ADD,Sym.as_idx(o),self.idx))
        def __sub__(self,o): return Sym(get_node(OP_SUB,self.idx,Sym.as_idx(o)))
        def __rsub__(self,o): return Sym(get_node(OP_SUB,Sym.as_idx(o),self.idx))
        def __mul__(self,o): return Sym(get_node(OP_MUL,self.idx,Sym.as_idx(o)))
        def __rmul__(self,o): return Sym(get_node(OP_MUL,Sym.as_idx(o),self.idx))
        def __neg__(self): return Sym(get_node(OP_NEG,self.idx,-1))
        def __pow__(self,p):
            if p==2: return self*self
            if p==1: return self
            if p==0: return Sym(ONE)
            raise ValueError
    class UM:
        @staticmethod
        def sin(x): return Sym(get_node(OP_SIN, Sym.as_idx(x), -1))
        @staticmethod
        def cos(x): return Sym(get_node(OP_COS, Sym.as_idx(x), -1))
    qs=[Sym(get_node(OP_INPUT,i,-1)) for i in range(n)]
    qds=[Sym(get_node(OP_INPUT,n+i,-1)) for i in range(n)]
    out=L(qs,qds,UM()); out_idx=Sym.as_idx(out)
    grads={out_idx: ONE}
    def add_grad(i,g):
        if i in grads: grads[i]=get_node(OP_ADD,grads[i],g)
        else: grads[i]=g
    for i in range(len(nodes)-1,-1,-1):
        g=grads.get(i)
        if g is None: continue
        op,a,b=nodes[i]
        if op==OP_ADD:
            add_grad(a,g); add_grad(b,g)
        elif op==OP_SUB:
            add_grad(a,g); add_grad(b,get_node(OP_NEG,g,-1))
        elif op==OP_MUL:
            add_grad(a,get_node(OP_MUL,g,b)); add_grad(b,get_node(OP_MUL,g,a))
        elif op==OP_NEG:
            add_grad(a,get_node(OP_NEG,g,-1))
        elif op==OP_SIN:
            add_grad(a,get_node(OP_MUL,g,get_node(OP_COS,a,-1)))
        elif op==OP_COS:
            add_grad(a,get_node(OP_MUL,g,get_node(OP_NEG,get_node(OP_SIN,a,-1),-1)))
    p=[grads.get(qds[i].idx, ZERO) for i in range(n)]
    f=[grads.get(qs[i].idx, ZERO) for i in range(n)]
    dot_cache={}
    def get_dot(idx):
        if idx in dot_cache: return dot_cache[idx]
        op,a,b=nodes[idx]
        if op==OP_INPUT:
            res=qds[a].idx if a<n else ZERO
        elif op==OP_ADD:
            res=get_node(OP_ADD,get_dot(a),get_dot(b))
        elif op==OP_SUB:
            res=get_node(OP_SUB,get_dot(a),get_dot(b))
        elif op==OP_MUL:
            res=get_node(OP_ADD,get_node(OP_MUL,get_dot(a),b),get_node(OP_MUL,a,get_dot(b)))
        elif op==OP_NEG:
            res=get_node(OP_NEG,get_dot(a),-1)
        elif op==OP_SIN:
            res=get_node(OP_MUL,get_node(OP_COS,a,-1),get_dot(a))
        elif op==OP_COS:
            res=get_node(OP_MUL,get_node(OP_NEG,get_node(OP_SIN,a,-1),-1),get_dot(a))
        else:
            res=ZERO
        dot_cache[idx]=res
        return res
    v=[get_dot(pi) for pi in p]
    jac_cache={}
    def get_jac(idx):
        if idx in jac_cache: return jac_cache[idx]
        op,a,b=nodes[idx]
        if op==OP_INPUT:
            res={a-n: ONE} if a>=n else {}
        elif op==OP_ADD or op==OP_SUB:
            da=get_jac(a); db=get_jac(b)
            if not da and not db: res={}
            else:
                keys=set(da)|set(db)
                res={}
                for k in keys: res[k]=get_node(op, da.get(k,ZERO), db.get(k,ZERO))
        elif op==OP_MUL:
            da=get_jac(a); db=get_jac(b)
            res={}
            if da:
                for k,vv in da.items():
                    res[k]=get_node(OP_ADD,res.get(k,ZERO),get_node(OP_MUL,vv,b))
            if db:
                for k,vv in db.items():
                    res[k]=get_node(OP_ADD,res.get(k,ZERO),get_node(OP_MUL,a,vv))
        elif op==OP_NEG:
            da=get_jac(a); res={k:get_node(OP_NEG,vv,-1) for k,vv in da.items()} if da else {}
        elif op==OP_SIN:
            da=get_jac(a)
            if da:
                c=get_node(OP_COS,a,-1)
                res={k:get_node(OP_MUL,c,vv) for k,vv in da.items()}
            else: res={}
        elif op==OP_COS:
            da=get_jac(a)
            if da:
                s=get_node(OP_NEG,get_node(OP_SIN,a,-1),-1)
                res={k:get_node(OP_MUL,s,vv) for k,vv in da.items()}
            else: res={}
        else: res={}
        jac_cache[idx]=res
        return res
    M_entries=[]
    for i in range(n):
        row=get_jac(p[i])
        for j,node in row.items():
            if j>=i: M_entries.append((i,j,node))
    rhs_nodes=[get_node(OP_SUB,f[i],v[i]) for i in range(n)]
    roots=[node for _,_,node in M_entries]+rhs_nodes
    used=set(); stack=roots[:]
    while stack:
        idx=stack.pop()
        if idx in used: continue
        used.add(idx)
        op,a,b=nodes[idx]
        if op==OP_CONST or op==OP_INPUT: continue
        if a!=-1: stack.append(a)
        if b!=-1: stack.append(b)
    old_to_new={}; new_nodes=[]
    for idx,item in enumerate(nodes):
        if idx in used:
            old_to_new[idx]=len(new_nodes)
            op,a,b=item
            na=old_to_new.get(a,-1) if a!=-1 else -1
            nb=old_to_new.get(b,-1) if b!=-1 else -1
            new_nodes.append((op,na,nb,item))
    opnd_sin={}; opnd_cos={}
    for i,(op,na,nb,orig) in enumerate(new_nodes):
        if op==OP_SIN: opnd_sin[na]=i
        elif op==OP_COS: opnd_cos[na]=i
    pair_first={}; skip=set()
    for opnd,si in opnd_sin.items():
        ci=opnd_cos.get(opnd)
        if ci is None: continue
        first=min(si,ci); pair_first[first]=(si,ci,opnd); skip.add(max(si,ci))
    lines=["#include <math.h>","#include <string.h>",
           "void cal_opt(double* __restrict q, double* __restrict qdot, double* __restrict qddot) {",
           f"  double w[{len(new_nodes)}];",
           f"  double M[{n*n}];",
           f"  double rhs[{n}];"]
    for i,(op,na,nb,orig) in enumerate(new_nodes):
        if i in pair_first:
            si,ci,opnd=pair_first[i]
            lines.append(f"  double s{i}, c{i}; __builtin_sincos(w[{opnd}], &s{i}, &c{i});")
            lines.append(f"  w[{si}] = s{i}; w[{ci}] = c{i};")
            continue
        if i in skip:
            lines.append(f"  /* w[{i}] computed by sincos */"); continue
        if op==OP_CONST:
            lines.append(f"  w[{i}] = {orig[1]:.17g};")
        elif op==OP_INPUT:
            idx=orig[1]
            lines.append(f"  w[{i}] = q[{idx}];" if idx<n else f"  w[{i}] = qdot[{idx-n}];")
        elif op==OP_ADD:
            lines.append(f"  w[{i}] = w[{na}] + w[{nb}];")
        elif op==OP_SUB:
            lines.append(f"  w[{i}] = w[{na}] - w[{nb}];")
        elif op==OP_MUL:
            lines.append(f"  w[{i}] = w[{na}] * w[{nb}];")
        elif op==OP_NEG:
            lines.append(f"  w[{i}] = -w[{na}];")
        elif op==OP_SIN:
            lines.append(f"  w[{i}] = sin(w[{na}]);")
        elif op==OP_COS:
            lines.append(f"  w[{i}] = cos(w[{na}]);")
        else:
            lines.append(f"  w[{i}] = 0.0;")
    lines.append("  memset(M, 0, sizeof(M));")
    for r,c,node in M_entries:
        wi=old_to_new.get(node)
        if wi is None: continue
        if r>=c: lines.append(f"  M[{r*n+c}] = w[{wi}];")
        else: lines.append(f"  M[{c*n+r}] = w[{wi}];")
    for i,node in enumerate(rhs_nodes):
        wi=old_to_new.get(node)
        lines.append(f"  rhs[{i}] = w[{wi}];" if wi is not None else f"  rhs[{i}] = 0.0;")
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
    src="\n".join(lines)
    key=hashlib.md5((src+str(flags)).encode()).hexdigest()
    cdir=os.path.join(tempfile.gettempdir(),"gc_opt_flagtest")
    os.makedirs(cdir, exist_ok=True)
    so_path=os.path.join(cdir,f"mod_{key}.so")
    if not os.path.exists(so_path):
        c_path=os.path.join(cdir,f"src_{key}.c")
        open(c_path,"w").write(src)
        cmd=["gcc","-shared","-fPIC","-o",so_path,c_path,"-lm"]+flags
        subprocess.check_call(cmd)
    lib=ctypes.CDLL(so_path)
    base=lib.cal_opt
    dblp=ctypes.POINTER(ctypes.c_double)
    base.argtypes=[dblp,dblp,dblp]
    base.restype=None
    _from=ctypes.c_double.from_buffer
    def cal(q,qd,qdd):
        base(_from(q), _from(qd), _from(qdd))
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
    L20 = make_synth_L(n, m_terms=100)
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
