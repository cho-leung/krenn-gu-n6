"""
INDEPENDENT exact decision engine for bi-colored weighted (n,d) problems,
written from scratch for the (6,3) audit (2026-09-03). No import of
computation/*.py.

Parameters:
  n          number of vertices
  coloring   dict edge (u,v) u<v -> (a,b) in {0,1,2}^2, or None (absent)
  mono_required  number of monochrome IVCs required (default 3)
  b_mixed    rhs for non-mono IVC equations (0 = exact problem; 1 = relaxed
             positive-control mode)

Returns (verdict, info) with the same verdict vocabulary as
computation/search_core.decide, but the logic is independently written.
All INFEASIBLE verdicts are certified by exact (rational) reasoning.
FEASIBLE verdicts carry an exact witness x; the caller can reconstruct
exact weights w_e via the Q-pseudoinverse when rank(U) = |S|.
"""
from itertools import combinations
import numpy as np
import sympy as sp

def _pms(vertices):
    out = []
    def rec(rem, cur):
        if not rem:
            out.append(sorted(cur)); return
        v0 = rem[0]
        for v1 in rem[1:]:
            rec([x for x in rem if x != v0 and x != v1], cur + [(v0, v1)])
    rec(sorted(vertices), [])
    return out

def decide_general(n, coloring, mono_required=3, b_mixed=0):
    V = list(range(n))
    EDGES = sorted(combinations(V, 2))
    PMS = _pms(V)
    MONO_CODE = [sum(i * 3**v for v in range(n)) for i in range(mono_required)]

    def ivc_code(M):
        code = 0
        for (u, v) in M:
            a, b = coloring[(u, v)]
            code += a * 3**u + b * 3**v
        return code

    S = [M for M in PMS if all(coloring[e] is not None for e in M)]
    present = [e for e in EDGES if coloring[e] is not None]
    codes = [ivc_code(M) for M in S]

    Pi = [[M for M, c in zip(S, codes) if c == MONO_CODE[i]] for i in range(mono_required)]
    if any(len(p) == 0 for p in Pi):
        return ("INFEASIBLE", {"reason": "missing monochrome IVC"})
    mixed = [(M, c) for M, c in zip(S, codes) if c not in MONO_CODE]
    groups = {}
    for M, c in mixed:
        groups.setdefault(c, []).append(M)
    singletons = [c for c, g in groups.items() if len(g) == 1]
    if singletons and b_mixed == 0:
        return ("INFEASIBLE", {"reason": "singleton non-mono IVC group (L3)"})

    idx = {tuple(M): j for j, M in enumerate(S)}
    rows, rhs = [], []
    for i in range(mono_required):
        rows.append([1 if tuple(M) in {tuple(m) for m in Pi[i]} else 0 for M in S])
        rhs.append(sp.Integer(1))
    for c, g in groups.items():
        rows.append([1 if tuple(M) in {tuple(m) for m in g} else 0 for M in S])
        rhs.append(sp.Integer(b_mixed))
    A = sp.Matrix(rows); b = sp.Matrix(rhs)
    rA = A.rank()
    if A.row_join(b).rank() > rA:
        return ("INFEASIBLE", {"reason": "linear system inconsistent"})

    U = sp.Matrix([[1 if e in M else 0 for e in present] for M in S])
    rels = U.T.nullspace()
    rels_int = []
    for rel in rels:
        den = sp.lcm([sp.fraction(v)[1] for v in rel])
        ivec = [int(sp.simplify(v * den)) for v in rel]
        g = sp.gcd(ivec)
        ivec = [v // g for v in ivec]
        if any(ivec):
            rels_int.append(ivec)

    sol = sp.linsolve((A, b))
    if sol is sp.S.EmptySet:
        return ("INFEASIBLE", {"reason": "linear system inconsistent (linsolve)"})
    solset = list(sol)
    free_syms = list(solset[0].free_symbols)
    subs0 = {s: sp.Integer(0) for s in free_syms}
    x0 = [sp.simplify(v.subs(subs0)) for v in solset[0]]
    Vk = [[sp.diff(v, s) for v in solset[0]] for s in free_syms]
    k = len(free_syms)
    nS = len(S)

    # all-nonzero: no coordinate identically zero on the affine space
    for m in range(nS):
        if x0[m] == 0 and all(Vk[j][m] == 0 for j in range(k)):
            return ("INFEASIBLE", {"reason": "coordinate identically zero"})

    t_syms = sp.symbols(f"t1:{k+1}")
    def coord(m):
        return x0[m] + sum(t_syms[j] * Vk[j][m] for j in range(k))

    polys = []
    for ivec in rels_int:
        pos = [m for m, c in enumerate(ivec) if c > 0]
        neg = [m for m, c in enumerate(ivec) if c < 0]
        lhs = sp.Integer(1)
        for m in pos: lhs *= coord(m) ** ivec[m]
        rhs_ = sp.Integer(1)
        for m in neg: rhs_ *= coord(m) ** (-ivec[m])
        polys.append(sp.expand(sp.simplify(lhs - rhs_)))

    def witness_at(tvals):
        xw = [sp.simplify(coord(m).subs(tvals)) for m in range(nS)]
        if all(v != 0 for v in xw):
            return xw
        return None

    if not polys:
        for tval in (1, 2, 3, -1, sp.Rational(1, 2)):
            xw = witness_at({s: tval for s in t_syms})
            if xw is not None:
                return ("FEASIBLE", {"witness": xw, "k": k})
        return ("UNRESOLVED", {"reason": "no generic nonzero point"})

    if k == 0:
        xw = x0
        for ivec in rels_int:
            lhs = sp.Integer(1); rhs_ = sp.Integer(1)
            for m, c in enumerate(ivec):
                if c > 0: lhs *= xw[m] ** c
                elif c < 0: rhs_ *= xw[m] ** (-c)
            if lhs != rhs_:
                return ("INFEASIBLE", {"reason": "unique solution violates lift relation"})
        if all(v != 0 for v in xw):
            return ("FEASIBLE", {"witness": xw, "k": 0})
        return ("INFEASIBLE", {"reason": "unique solution has zero coordinate"})

    if all(sp.simplify(F) == 0 for F in polys):
        xw = witness_at({s: sp.Integer(1) for s in t_syms})
        if xw is not None:
            return ("FEASIBLE", {"witness": xw, "k": k, "method": "L in image"})
        return ("UNRESOLVED", {"reason": "L in image but generic point has zeros"})

    if k == 1:
        gpoly = polys[0]
        for F in polys[1:]:
            gpoly = sp.gcd(sp.Poly(gpoly.as_expr(), t_syms[0]),
                           sp.Poly(sp.expand(F), t_syms[0]))
            if gpoly.is_one or (gpoly.is_number and gpoly != 0):
                return ("INFEASIBLE", {"reason": "relation gcd has no roots (k=1)"})
        try:
            roots = sp.Poly(gpoly, t_syms[0]).all_roots()
            for r in roots:
                xw = witness_at({t_syms[0]: r})
                if xw is not None:
                    return ("FEASIBLE", {"witness": xw, "k": 1, "method": "k1-gcd"})
        except Exception:
            pass
        return ("INFEASIBLE", {"reason": "no nonzero witness among all roots (k=1)"})

    # k >= 2: numeric search for FEASIBLE only; INFEASIBLE never certified here
    rng = np.random.default_rng(7)
    f = sp.lambdify(t_syms, polys, modules='numpy')
    jac = [[sp.diff(F, s) for s in t_syms] for F in polys]
    jf = sp.lambdify(t_syms, jac, modules='numpy')
    for _ in range(24):
        t = rng.standard_normal(k) + 1j * rng.standard_normal(k)
        for _ in range(60):
            Fv = np.array(f(*t), dtype=complex)
            Jv = np.array(jf(*t), dtype=complex)
            if not np.all(np.isfinite(Fv)) or not np.all(np.isfinite(Jv)):
                break
            t = t + np.linalg.lstsq(Jv, -Fv, rcond=None)[0]
            if np.max(np.abs(Fv)) < 1e-10:
                break
        if np.max(np.abs(np.array(f(*t), dtype=complex))) > 1e-8:
            continue
        try:
            t_exact = [sp.nsimplify(z, tolerance=1e-8) for z in t]
            if all(sp.simplify(F.subs(dict(zip(t_syms, t_exact)))) == 0 for F in polys):
                xw = witness_at(dict(zip(t_syms, t_exact)))
                if xw is not None:
                    return ("FEASIBLE", {"witness": xw, "k": k, "method": "numeric+nsimplify"})
        except Exception:
            continue
    if k <= 3:
        try:
            gb = sp.groebner(polys, *t_syms, order="lex")
            if gb and gb[0].is_number and gb[0] != 0:
                return ("INFEASIBLE", {"reason": "groebner basis [1]"})
            for s in t_syms[1:]:
                fixed = {s2: sp.Rational(1) for s2 in t_syms[1:]}
                F1 = [sp.expand(F.subs(fixed)) for F in polys if sp.expand(F.subs(fixed)) != 0]
                if not F1:
                    break
                roots = sp.solve(sp.Poly(F1[0], t_syms[0]), t_syms[0])
                for r in roots:
                    tvals = {t_syms[0]: r, **fixed}
                    if all(sp.simplify(F.subs(tvals)) == 0 for F in polys):
                        xw = witness_at(tvals)
                        if xw is not None:
                            return ("FEASIBLE", {"witness": xw, "k": k, "method": "symbolic"})
        except Exception:
            pass
    return ("UNRESOLVED", {"reason": "relation system unsolved", "k": k})

def exact_weights(n, coloring, xvec):
    """Exact complex weights w_e with prod_{e in M} w_e == x_M for all S,
    via the Q-pseudoinverse a = U^T (U U^T)^{-1} (requires rank(U)=|S|)."""
    V = list(range(n))
    EDGES = sorted(combinations(V, 2))
    PMS = _pms(V)
    S = [M for M in PMS if all(coloring[e] is not None for e in M)]
    present = [e for e in EDGES if coloring[e] is not None]
    U = sp.Matrix([[1 if e in M else 0 for e in present] for M in S])
    assert U.rows == len(xvec) and U.rank() == U.rows, "pseudoinverse requires full row rank"
    G = U * U.T
    a = U.T * G.inv()           # |E| x |S| over Q
    w = {}
    for j, e in enumerate(present):
        w[e] = sp.Integer(1)
        for m, xM in enumerate(xvec):
            w[e] = sp.simplify(w[e] * xM ** a[j, m])
    return w, S
