"""
Krenn-Gu (6,3) exact decision procedure.

Given a coloring of the 15 edges of K_6 (each edge: color pair (a,b) in
{0,1,2}^2, or ABSENT = zero weight), decide whether there exist complex
weights (all nonzero, WLOG) realizing a monochromatic graph of dimension 3,
and if so, produce an exact witness.

Reductions used (recorded in research_os):
  R1 (all-nonzero WLOG): zero-weight edges can be deleted; a surviving
     solution has all weights nonzero.
  R2 (K6 suffices for simple): mu(G) <= mu(K_6) for any simple 6-vertex G,
     since colorings extend with zero weights.
  R3 (mono PMs): a PM has monochromatic IVC color i  iff  all its edges are
     colored (i,i).  So P_i = PMs of the color-i monochrome subgraph H_i.
  R4 (per-IVC decomposition): the 729 equations decompose per coloring:
     w(ccc) = sum_{M in P_c} prod(M) = 1,  and every realized non-mono IVC
     must sum to 0.  Unrealized IVCs are automatically 0.
  R5 (liftability): x_M = prod_{e in M} w_e is realizable (x in (C*)^15)
     iff  prod_M x_M^{c_M} = 1 for every relation c in ker(U^T), where U is
     the PM-edge incidence matrix (rank 10 for K_6, 5 relations).
  R6 (generic threshold): an affine solution space of dim k intersects the
     10-dim image generically iff k >= 5; k < 5 cases are solved exactly.

Decision: build linear system A x = b from the realized IVC groups
(3 mono + g non-mono equations); compute its solution space L over Q;
intersect L with the image (relations), avoiding coordinate hyperplanes
(all x_M != 0).  FEASIBLE -> exact witness vector x (rational or algebraic),
INFEASIBLE -> certified reason (or computational search failure -> UNRESOLVED).
"""
from itertools import combinations
import numpy as np
import sympy as sp
from k6_basics import V, EDGES, EIDX, PMS, PM_EDGES

ABSENT = None
OPTS = [(a, b) for a in range(3) for b in range(3)]   # 9 color-pair options
OPT_A = [o[0] for o in OPTS]
OPT_B = [o[1] for o in OPTS]
MONO_CODE = [sum(c * 3**v for v, c in enumerate((i,)*6)) for i in range(3)]

def ivc_code(pm, coloring):
    """Base-3 code of the IVC of perfect matching pm under edge->(a,b) coloring."""
    code = 0
    for (u, v) in pm:
        a, b = coloring[(u, v)]
        code += a * 3**u + b * 3**v
    return code

def pm_list_from_coloring(coloring):
    """PMs present in the subgraph (edges != ABSENT), as lists of edges."""
    return [M for M in PM_EDGES if all(coloring[e] is not ABSENT for e in M)]

def decide(coloring, verbose=False):
    """
    Return (verdict, info):
      verdict in {FEASIBLE, INFEASIBLE, UNRESOLVED}
      info: dict with reason / witness x (sympy values) / diagnostics.
    """
    S = pm_list_from_coloring(coloring)
    present_edges = [e for e in EDGES if coloring[e] is not ABSENT]
    codes = [ivc_code(M, coloring) for M in S]

    # --- mono PM sets and linear system ---
    Pi = [[M for M, c in zip(S, codes) if c == MONO_CODE[i]] for i in range(3)]
    if any(len(p) == 0 for p in Pi):
        return ("INFEASIBLE", {"reason": "missing monochrome IVC (some color has no PM)"})
    mixed = [(M, c) for M, c in zip(S, codes) if c not in MONO_CODE]
    groups = {}
    for M, c in mixed:
        groups.setdefault(c, []).append(M)

    # all-nonzero requires every realized non-mono IVC to have >= 2 PMs
    singletons = [c for c, g in groups.items() if len(g) == 1]
    if singletons:
        return ("INFEASIBLE", {"reason": f"singleton non-mono IVC groups: {len(singletons)}"})

    # linear system A x = b over Q: x indexed by S
    idx = {tuple(M): j for j, M in enumerate(S)}
    rows, rhs = [], []
    for i in range(3):
        rows.append([1 if tuple(M) in {tuple(m) for m in Pi[i]} else 0 for M in S])
        rhs.append(sp.Integer(1))
    for c, g in groups.items():
        rows.append([1 if tuple(M) in {tuple(m) for m in g} else 0 for M in S])
        rhs.append(sp.Integer(0))
    A = sp.Matrix(rows)
    b = sp.Matrix(rhs)
    r = A.rank()
    # consistency
    aug = A.row_join(b)
    if aug.rank() > r:
        return ("INFEASIBLE", {"reason": "linear system inconsistent"})
    n = len(S)
    k = n - r   # dimension of solution space

    # relations from ker U^T
    U = sp.Matrix([[1 if e in M else 0 for e in present_edges] for M in S])
    rels = U.T.nullspace()

    def x_is_zero_identically(x0, Vk, m):
        # check linear form x_m(t) == 0 identically on the solution space
        return x0[m] == 0 and all(v[m] == 0 for v in Vk)

    # --- solve ---
    # particular solution + kernel basis over Q
    x0 = [sp.Integer(0)] * n
    Vk = []
    sol = sp.linsolve((A, b))
    if sol is not sp.S.EmptySet:
        solset = list(sol)
        if solset:
            free_syms = list(solset[0].free_symbols)
            subs = {s: sp.Integer(0) for s in free_syms}
            x0 = [sp.simplify(v.subs(subs)) for v in solset[0]]
            # kernel basis: derivatives w.r.t. each free symbol
            for s in free_syms:
                Vk.append([sp.diff(v, s) for v in solset[0]])
            k = len(free_syms)  # true dimension
    else:
        return ("INFEASIBLE", {"reason": "linear system inconsistent (linsolve)"})

    # all-nonzero: no coordinate identically zero
    for m in range(n):
        if x_is_zero_identically(x0, Vk, m):
            return ("INFEASIBLE", {"reason": f"x_M identically zero (M index {m})"})

    # liftability relations: F_j(t) = prod_{c>0} x^c - prod_{c<0} x^{-c} = 0
    t_syms = sp.symbols(f"t1:{k+1}")
    polys = []
    for rel in rels:
        # scale to integers
        den = sp.lcm([sp.fraction(v)[1] for v in rel])
        ivec = [int(sp.simplify(v * den)) for v in rel]
        g = sp.gcd(ivec)
        ivec = [v // g for v in ivec]
        pos = [m for m, c in enumerate(ivec) if c > 0]
        neg = [m for m, c in enumerate(ivec) if c < 0]
        if not pos and not neg:
            continue
        xm = []
        for m in range(n):
            expr = x0[m] + sum(t_syms[j] * Vk[j][m] for j in range(k))
            xm.append(expr)
        lhs = sp.Integer(1)
        for m in pos:
            lhs *= xm[m] ** ivec[m]
        rhs_p = sp.Integer(1)
        for m in neg:
            rhs_p *= xm[m] ** (-ivec[m])
        polys.append(sp.expand(sp.simplify(lhs - rhs_p)))

    if not polys:
        # no relations: any nonzero point in L lifts -> FEASIBLE with rational witness
        x_wit = [x0[m] if x0[m] != 0 else sp.Integer(1) for m in range(n)]
        # if some x0[m] == 0 but not identically: nudge via kernel; generic t=1
        t_vals = {s: sp.Integer(1) for s in t_syms}
        x_wit = [sp.simplify((x0[m] + sum(t_syms[j] * Vk[j][m] for j in range(k))).subs(t_vals)) for m in range(n)]
        if all(v != 0 for v in x_wit):
            return ("FEASIBLE", {"witness": x_wit, "k": k, "g": len(groups), "S": S, "codes": codes})
        # try a few generic substitutions
        for t_val in (2, 3, -1, sp.Rational(1, 2)):
            t_vals = {s: t_val for s in t_syms}
            x_wit = [sp.simplify((x0[m] + sum(t_syms[j] * Vk[j][m] for j in range(k))).subs(t_vals)) for m in range(n)]
            if all(v != 0 for v in x_wit):
                return ("FEASIBLE", {"witness": x_wit, "k": k, "g": len(groups), "S": S, "codes": codes})
        return ("UNRESOLVED", {"reason": "no generic nonzero point found"})

    # polys are in t1..tk with rational coefficients
    if k == 0:
        # unique x: verify relations exactly (pure integer/rational arithmetic)
        x_wit = x0
        for rel in rels:
            den = sp.lcm([sp.fraction(v)[1] for v in rel])
            ivec = [int(sp.simplify(v * den)) for v in rel]
            g = sp.gcd(ivec)
            ivec = [v // g for v in ivec]
            lhs = sp.Integer(1); rhs_ = sp.Integer(1)
            for m, c in enumerate(ivec):
                if c > 0:
                    lhs *= sp.Rational(x_wit[m]) ** c
                elif c < 0:
                    rhs_ *= sp.Rational(x_wit[m]) ** (-c)
            if lhs != rhs_:
                return ("INFEASIBLE", {"reason": "unique linear solution violates a lift relation"})
        if all(v != 0 for v in x_wit):
            return ("FEASIBLE", {"witness": x_wit, "k": 0, "g": len(groups), "S": S, "codes": codes})
        return ("INFEASIBLE", {"reason": "unique solution has zero coordinate"})

    # k >= 1: check for identically-zero polys (L inside image -> any point works)
    all_zero = all(sp.simplify(F) == 0 for F in polys)
    if all_zero:
        t_vals = {s: sp.Integer(1) for s in t_syms}
        x_wit = [sp.simplify((x0[m] + sum(t_syms[j] * Vk[j][m] for j in range(k))).subs(t_vals)) for m in range(n)]
        if all(v != 0 for v in x_wit):
            return ("FEASIBLE", {"witness": x_wit, "k": k, "g": len(groups), "S": S, "codes": codes})
        return ("UNRESOLVED", {"reason": "image contains L but generic point has zeros"})

    # k >= 1: solve F(t) = 0.
    if k == 1:
        # gcd chain: common roots of all polys (exact infeasibility when gcd = const)
        gpoly = polys[0]
        for F in polys[1:]:
            gpoly = sp.gcd(sp.Poly(sp.expand(gpoly), t_syms[0]),
                           sp.Poly(sp.expand(F), t_syms[0]))
            if gpoly.is_one or (gpoly.is_number and gpoly != 0):
                return ("INFEASIBLE", {"reason": "relation gcd has no roots (k=1)"})
        # gpoly has roots over C; find one avoiding zero coordinates
        try:
            roots = sp.Poly(gpoly, t_syms[0]).all_roots()
        except Exception:
            roots = sp.Poly(gpoly, t_syms[0]).nroots()
        cand = [r for r in roots if sp.simplify(gpoly.subs(t_syms[0], r)) == 0]
        if not cand and roots:
            cand = roots
        for root in cand:
            x_wit = [sp.simplify((x0[i] + t_syms[0] * Vk[0][i]).subs(t_syms[0], root)) for i in range(len(x0))]
            if all(v != 0 for v in x_wit):
                return ("FEASIBLE", {"witness": x_wit, "k": 1, "g": len(groups), "S": S, "codes": codes,
                                     "method": "k1-gcd"})
        return ("INFEASIBLE", {"reason": "all roots hit zero coordinates (k=1)"})
    # k >= 2: numeric Newton + exact nsimplify first (fast), then groebner for k <= 3
    wit = _numeric_solve_and_verify(polys, t_syms, x0, Vk, k, verbose)
    if wit is not None:
        return ("FEASIBLE", {"witness": wit, "k": k, "g": len(groups), "S": S, "codes": codes,
                             "method": "numeric+nsimplify"})
    if k <= 3:
        try:
            gb = sp.groebner(polys, *t_syms, order="lex")
            if gb and gb[0].is_number and gb[0] != 0:
                return ("INFEASIBLE", {"reason": "groebner basis [1] (k>=2)"})
            wit = _symbolic_solve(polys, t_syms, x0, Vk, k)
            if wit is not None:
                return ("FEASIBLE", {"witness": wit, "k": k, "g": len(groups), "S": S, "codes": codes,
                                     "method": "symbolic"})
        except Exception:
            pass
    return ("UNRESOLVED", {"reason": "relation system unsolved", "k": k, "g": len(groups),
                            "npolys": len(polys)})

def _lambdify_vec(polys, syms):
    from sympy.utilities.lambdify import lambdify
    f = lambdify(syms, polys, modules='numpy')
    jac = [[sp.diff(F, s) for s in syms] for F in polys]
    jacf = lambdify(syms, jac, modules='numpy')
    return f, jacf

def _numeric_solve_and_verify(polys, t_syms, x0, Vk, k, verbose, restarts=24):
    """Newton on F(t)=0 over C; verify exact via sympy nsimplify."""
    f, jacf = _lambdify_vec(polys, t_syms)
    m = len(polys)
    rng = np.random.default_rng(42)
    for attempt in range(restarts):
        t = rng.standard_normal(k) * (0.5 + 0.5 * attempt / restarts) + \
            1j * rng.standard_normal(k) * (0.5 + 0.5 * attempt / restarts)
        for it in range(60):
            Fv = np.array(f(*t), dtype=complex)
            Jv = np.array(jacf(*t), dtype=complex)
            if np.any(~np.isfinite(Fv)) or np.any(~np.isfinite(Jv)):
                break
            # minimum-norm Newton step (works for both over/underdetermined)
            step = np.linalg.lstsq(Jv, -Fv, rcond=None)[0]
            t = t + step
            if np.max(np.abs(Fv)) < 1e-10:
                break
        Fv = np.array(f(*t), dtype=complex)
        if np.max(np.abs(Fv)) > 1e-8:
            continue
        # attempt exact reconstruction
        try:
            t_exact = [sp.nsimplify(sp.nsimplify(z, tolerance=1e-8), [sp.pi, sp.I],
                                    tolerance=1e-8) for z in t]
            ok = True
            for F in polys:
                val = sp.simplify(F.subs(dict(zip(t_syms, t_exact))))
                if val != 0:
                    ok = False
                    break
            if ok:
                x_wit = [sp.simplify((x0[i] + sum(t_syms[j] * Vk[j][i] for j in range(k)))
                                     .subs(dict(zip(t_syms, t_exact)))) for i in range(len(x0))]
                if all(v != 0 for v in x_wit):
                    return x_wit
        except Exception:
            continue
    return None

def _symbolic_solve(polys, t_syms, x0, Vk, k):
    """Symbolic fallback: fix all but min(k,1) free coords generically, solve."""
    if k >= 1:
        try:
            fixed = {s: sp.Rational(1) for s in t_syms[1:]}
            F1 = [sp.expand(F.subs(fixed)) for F in polys if sp.expand(F.subs(fixed)) != 0]
            if not F1:
                return None
            roots = sp.solve(sp.Poly(F1[0], t_syms[0]), t_syms[0]) if F1 else []
            # need ALL polys to vanish at the root
            for root in roots:
                tvals = {t_syms[0]: root}
                tvals.update(fixed)
                if all(sp.simplify(F.subs(tvals)) == 0 for F in polys):
                    x_wit = [sp.simplify((x0[i] + sum(t_syms[j] * Vk[j][i] for j in range(k)))
                                         .subs(tvals)) for i in range(len(x0))]
                    if all(v != 0 for v in x_wit):
                        return x_wit
        except Exception:
            return None
    return None
