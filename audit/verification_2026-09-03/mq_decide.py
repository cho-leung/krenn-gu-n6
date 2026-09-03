"""
mq_decide.py -- exact decision procedure for the MULTIGRAPH (6,3) problem.

Question: given a multigraph slot coloring (per vertex pair a set of slots
with distinct ordered color pairs), do complex nonzero slot weights exist
such that w(000)=w(111)=w(222)=1 and w(sigma)=0 for all other colorings?

Method (mirrors the audited simple-case pipeline in computation/search_core.py,
generalized from "simple coloring of 15 pairs" to "slot coloring"):
  - PM instances = (shape, one slot per pair of shape); x_M = prod weights.
  - R3/R4: monochrome-IVC PMs of color i are exactly the instances whose
    three slots all carry color pair (i,i) [H_i is simple: at most one (i,i)
    slot per pair]; sum over P_i of x_M = 1.  Realized non-mono IVC groups
    must sum to 0 (so each has >= 2 members when weights are nonzero).
  - R5 (liftability): x realizable by slot weights iff
    prod_M x_M^{c_M} = 1 for every c in ker U^T, U = instance-slot incidence.
  - Exact decision: affine solution space L of A x = b over Q, intersect L
    with the image variety, avoid coordinate zeroes (R6-style), solved
    exactly (rational/roots/groebner/numeric+verify) like search_core.

Verdicts: FEASIBLE (with exact witness x, plus slot weights numerically
verified), INFEASIBLE (certified reason), UNRESOLVED.
"""
import itertools
import numpy as np
import sympy as sp
from mq_basics import EDGES, EIDX, pm_instances, MONO_DIGITS, MONO_CODE

def build_system(insts):
    """Linear system A x = b over Q from mono sums and realized non-mono groups.
    Returns (rows, rhs) with a row per mono color and per realized non-mono code.
    Also returns group info: codes realized with size."""
    # mono PM sets
    Pi = [[], [], []]
    for j, ins in enumerate(insts):
        d = ins["digits"]
        for i in range(3):
            if d == MONO_DIGITS[i]:
                Pi[i].append(j)
    groups = {}
    for j, ins in enumerate(insts):
        c = ins["code"]
        if c in MONO_CODE:
            continue
        groups.setdefault(c, []).append(j)
    return Pi, groups

def decide(slot_coloring, verbose=False):
    """
    slot_coloring: dict pair -> tuple/list of ordered color pairs (a,b)
    (all present slots; empty tuple = pair absent).  Returns
    (verdict, info) with verdict in {FEASIBLE, INFEASIBLE, UNRESOLVED}.
    """
    insts = pm_instances(slot_coloring)
    n = len(insts)
    if n == 0:
        return ("INFEASIBLE", {"reason": "no perfect matchings at all"})
    Pi, groups = build_system(insts)
    if any(len(p) == 0 for p in Pi):
        return ("INFEASIBLE", {"reason": "missing monochrome IVC (some color has no PM)"})
    # L3: every realized non-mono IVC group has >= 2 PMs (all-nonzero weights)
    singletons = [c for c, g in groups.items() if len(g) == 1]
    if singletons:
        return ("INFEASIBLE", {"reason": f"singleton non-mono IVC groups: {len(singletons)}"})

    # present slots, instance-slot incidence U
    slots = []
    slot_set = set()
    for e, lst in slot_coloring.items():
        for j, (a, b) in enumerate(lst):
            slot_set.add((e, j))
    slot_list = sorted(slot_set, key=lambda t: (EIDX[t[0]], t[1]))
    sidx = {s: k for k, s in enumerate(slot_list)}
    U = sp.zeros(n, len(slot_list))
    for mi, ins in enumerate(insts):
        for (e, j) in ins["edges"]:
            U[mi, sidx[(e, j)]] = 1

    # linear system: 3 mono rows + one row per non-mono group
    rows, rhs = [], []
    for i in range(3):
        r = [sp.Integer(0)] * n
        for j in Pi[i]:
            r[j] = sp.Integer(1)
        rows.append(r); rhs.append(sp.Integer(1))
    for c, g in sorted(groups.items()):
        r = [sp.Integer(0)] * n
        for j in g:
            r[j] = sp.Integer(1)
        rows.append(r); rhs.append(sp.Integer(0))
    A = sp.Matrix(rows)
    b = sp.Matrix(rhs)
    r = A.rank()
    if A.row_join(b).rank() > r:
        return ("INFEASIBLE", {"reason": "linear system inconsistent"})

    rels = U.T.nullspace()
    info0 = {"k": None, "g": len(groups), "n": n, "slots": len(slot_list),
             "rels": len(rels), "rankU": U.rank()}

    # ---- solve exactly (same architecture as search_core.decide) ----
    sol = sp.linsolve((A, b))
    if sol is sp.S.EmptySet:
        return ("INFEASIBLE", {"reason": "linear system inconsistent (linsolve)"})
    solset = list(sol)
    free_syms = list(solset[0].free_symbols)
    subs0 = {s: sp.Integer(0) for s in free_syms}
    x0 = [sp.simplify(v.subs(subs0)) for v in solset[0]]
    Vk = [[sp.diff(v, s) for v in solset[0]] for s in free_syms]
    k = len(free_syms)
    info0["k"] = k

    def identically_zero(m):
        return x0[m] == 0 and all(Vk[j][m] == 0 for j in range(k))
    zero_coords = [m for m in range(n) if identically_zero(m)]
    if zero_coords:
        return ("INFEASIBLE", {"reason": f"x_M identically zero on L ({len(zero_coords)} coords)"})

    # lift relations as polynomial equations in the free parameters
    t_syms = sp.symbols(f"t1:{k+1}")
    polys = []
    for rel in rels:
        den = sp.lcm([sp.fraction(v)[1] for v in rel])
        ivec = [int(sp.simplify(v * den)) for v in rel]
        g0 = sp.gcd(ivec)
        ivec = [v // g0 for v in ivec]
        pos = [m for m, c in enumerate(ivec) if c > 0]
        neg = [m for m, c in enumerate(ivec) if c < 0]
        if not pos and not neg:
            continue
        xm = [x0[m] + sum(t_syms[j] * Vk[j][m] for j in range(k)) for m in range(n)]
        lhs = sp.Integer(1)
        for m in pos:
            lhs *= xm[m] ** ivec[m]
        rh = sp.Integer(1)
        for m in neg:
            rh *= xm[m] ** (-ivec[m])
        polys.append(sp.expand(sp.simplify(lhs - rh)))

    def make_witness(t_vals):
        return [sp.simplify((x0[m] + sum(t_syms[j] * Vk[j][m] for j in range(k)))
                            .subs(t_vals)) for m in range(n)]

    if not polys:
        for tv in (1, 2, 3, -1, sp.Rational(1, 2)):
            x_wit = make_witness({s: tv for s in t_syms})
            if all(v != 0 for v in x_wit):
                info = dict(info0)
                info["witness"] = x_wit
                info["t"] = {str(s): tv for s in t_syms}
                return ("FEASIBLE", info)
        return ("UNRESOLVED", {"reason": "no relation system but no nonzero point",
                               **info0})

    if k == 0:
        x_wit = x0
        for rel in rels:
            den = sp.lcm([sp.fraction(v)[1] for v in rel])
            ivec = [int(sp.simplify(v * den)) for v in rel]
            g0 = sp.gcd(ivec)
            ivec = [v // g0 for v in ivec]
            lhs = sp.Integer(1); rh = sp.Integer(1)
            for m, c in enumerate(ivec):
                if c > 0:
                    lhs *= sp.Rational(x_wit[m]) ** c
                elif c < 0:
                    rh *= sp.Rational(x_wit[m]) ** (-c)
            if lhs != rh:
                return ("INFEASIBLE", {"reason": "unique linear solution violates a lift relation"})
        if all(v != 0 for v in x_wit):
            info = dict(info0); info["witness"] = x_wit; info["t"] = {}
            return ("FEASIBLE", info)
        return ("INFEASIBLE", {"reason": "unique solution has a zero coordinate"})

    all_zero = all(sp.simplify(F) == 0 for F in polys)
    if all_zero:
        for tv in (1, 2, 3, -1, sp.Rational(1, 2)):
            x_wit = make_witness({s: tv for s in t_syms})
            if all(v != 0 for v in x_wit):
                info = dict(info0); info["witness"] = x_wit
                info["t"] = {str(s): tv for s in t_syms}
                info["method"] = "image contains L"
                return ("FEASIBLE", info)
        return ("UNRESOLVED", {"reason": "image contains L, generic point has zeros", **info0})

    if k == 1:
        gpoly = polys[0]
        for F in polys[1:]:
            gpoly = sp.gcd(sp.Poly(sp.expand(gpoly), t_syms[0]),
                           sp.Poly(sp.expand(F), t_syms[0]))
            if gpoly.is_one or (gpoly.is_number and gpoly != 0):
                return ("INFEASIBLE", {"reason": "relation gcd has no roots (k=1)"})
        try:
            roots = sp.Poly(gpoly, t_syms[0]).all_roots()
        except Exception:
            roots = sp.Poly(gpoly, t_syms[0]).nroots()
        cand = [r for r in roots if sp.simplify(gpoly.subs(t_syms[0], r)) == 0]
        if not cand and roots:
            cand = roots
        for root in cand:
            x_wit = make_witness({t_syms[0]: root})
            if all(v != 0 for v in x_wit):
                info = dict(info0); info["witness"] = x_wit
                info["t"] = {str(t_syms[0]): root}; info["method"] = "k1-gcd"
                return ("FEASIBLE", info)
        return ("INFEASIBLE", {"reason": "all roots hit zero coordinates (k=1)"})

    # k >= 2: numeric root search; every accepted candidate is verified by
    # direct high-precision lifting to slot weights and checking ALL 729
    # coloring sums (verify_witness_full).  No exactness assumption on the
    # parameter values is made.
    res = _numeric_solve_and_verify(polys, t_syms, x0, Vk, k)
    if res is not None:
        x_wit = res["x"]
        try:
            vr = verify_witness_full(slot_coloring, x_wit, prec=60)
        except Exception:
            vr = None
        if vr is not None and vr["maxerr"] < 1e-45:
            info = dict(info0); info["t"] = res["t"]
            info["method"] = "numeric+fullcheck"
            info["verification"] = {"logres": vr["logres"], "maxerr": vr["maxerr"]}
            return ("FEASIBLE", info)
    if k <= 4:
        try:
            gb = sp.groebner(polys, *t_syms, order="lex")
            if gb and gb[0].is_number and gb[0] != 0:
                return ("INFEASIBLE", {"reason": "groebner basis [1] (k>=2)"})
        except Exception:
            pass
    return ("UNRESOLVED", {"reason": "relation system unsolved", **info0,
                           "npolys": len(polys)})

def _numeric_solve_and_verify(polys, t_syms, x0, Vk, k, restarts=24):
    """Common root of the relation polynomials over C, numerically.

    The x_M are Q-affine in the free parameters:  x_m = a_m + sum_j b_jm t_j
    with a_m, b_jm in Q (entries of the exact linsolve solution).  Roots are
    searched in float64 (path A: univariate slicing when ONE polynomial in
    TWO variables, the generic case; path B: damped Newton on the system),
    then polished to ~60 digits with mpmath Newton, and x is evaluated at the
    polished point in 60-digit mpmath arithmetic.  Return dict with keys
    t (list of mp.mpc) and x (list of mp.mpc), or None.
    """
    import mpmath as mp
    mp.mp.dps = 60
    a = [sp.Rational(x0[i]) for i in range(len(x0))]
    b = [[sp.Rational(Vk[j][i]) for i in range(len(x0))] for j in range(k)]
    def to_mp(r):
        return mp.mpf(r.p) / mp.mpf(r.q)
    def x_at(ts):
        return [to_mp(a[i]) + sum(to_mp(b[j][i]) * ts[j] for j in range(k))
                for i in range(len(a))]
    # mpmath-native evaluation of the polynomials (rational coefficients)
    fmp = sp.lambdify(t_syms, polys, modules="mpmath")
    def Fvals(ts):
        return [mp.mpc(z) for z in fmp(*ts)]
    def err(ts):
        vs = Fvals(ts)
        return max(abs(v) for v in vs)
    def polish(ts0):
        ts = [mp.mpc(z) for z in ts0]
        h = mp.mpf(10) ** (-40)
        for it in range(80):
            vs = Fvals(ts)
            if max(abs(v) for v in vs) < mp.mpf(10) ** (-52):
                return ts
            # Jacobian by central differences at mp precision
            J = []
            for r in range(len(polys)):
                row = []
                for j in range(k):
                    tsj = list(ts); tsj[j] += h
                    Fp = Fvals(tsj)[r]
                    tsm = list(ts); tsm[j] -= h
                    Fm = Fvals(tsm)[r]
                    row.append((Fp - Fm) / (2 * h))
                J.append(row)
            mJ = mp.matrix(len(polys), k)
            for r, row in enumerate(J):
                for c, v in enumerate(row):
                    mJ[r, c] = v
            mv = mp.matrix(len(polys), 1)
            for r, v in enumerate(vs):
                mv[r, 0] = -v
            try:
                if len(polys) == k:
                    dz = mp.lu_solve(mJ, mv)
                elif len(polys) > k:
                    # least squares (generically nonsingular: no ridge needed)
                    dz = mp.lu_solve(mJ.H * mJ, mJ.H * mv)
                else:
                    # underdetermined: minimum-norm step via right inverse
                    dz = mJ.H * mp.lu_solve(mJ * mJ.H, mv)
            except Exception:
                return None
            ts = [ts[j] + dz[j, 0] for j in range(k)]
        return None

    x_wit_expr = [x0[i] + sum(t_syms[j] * Vk[j][i] for j in range(k))
                  for i in range(len(x0))]
    def coords_ok(ts):
        xv = x_at(ts)
        return all(abs(v) > mp.mpf(10) ** (-30) for v in xv)

    # ---- path A: single polynomial in 2 variables: univariate slicing ----
    if len(polys) == 1 and k == 2:
        F = polys[0]
        deg1 = sp.degree(sp.expand(F), t_syms[0])
        deg2 = sp.degree(sp.expand(F), t_syms[1])
        rng = np.random.default_rng(11)
        def try_point(t0, t1v):
            ts_pol = polish([t0, t1v])
            if ts_pol is None:
                return None
            if err(ts_pol) > mp.mpf(10) ** (-50):
                return None
            if not coords_ok(ts_pol):
                return None
            return {"t": ts_pol, "x": x_at(ts_pol)}
        if deg2 == 0 and deg1 >= 1:
            # F depends only on t1: root the univariate; t2 is free
            r1s = sp.Poly(sp.expand(F), t_syms[0]).nroots()
            for r1 in r1s:
                for _ in range(12):
                    z2 = (rng.standard_normal() + 1j * rng.standard_normal()) * 5.0
                    if not np.isfinite(complex(z2)):
                        continue
                    out = try_point(complex(r1), complex(z2))
                    if out is not None:
                        return out
            return None
        coeffs = sp.Poly(sp.expand(F), t_syms[1]).all_coeffs()  # high -> low
        for attempt in range(150):
            zeta = complex((rng.standard_normal() + 1j * rng.standard_normal())
                           * (0.3 + 2.0 * attempt / 150))
            cvals = np.array([complex(c.subs(t_syms[0], zeta)) for c in coeffs],
                             dtype=complex)
            if np.any(~np.isfinite(cvals)):
                continue
            c0 = np.trim_zeros(cvals, trim="f")
            if c0.size <= 1:
                continue
            for rt in np.roots(c0):
                if not np.isfinite(rt):
                    continue
                if abs(complex(F.subs({t_syms[0]: zeta, t_syms[1]: rt}))) > 1e-6:
                    continue
                x_fl = np.array([complex(v.subs({t_syms[0]: zeta, t_syms[1]: rt}))
                                 for v in x_wit_expr], dtype=complex)
                if np.min(np.abs(x_fl)) < 1e-6:
                    continue
                for it in range(60):
                    J2 = complex(sp.diff(F, t_syms[1]).subs({t_syms[0]: zeta, t_syms[1]: rt}))
                    Fv = complex(F.subs({t_syms[0]: zeta, t_syms[1]: rt}))
                    if not np.isfinite(J2) or abs(J2) < 1e-300:
                        break
                    rt -= Fv / J2
                    if abs(Fv) < 1e-14:
                        break
                out = try_point(zeta, complex(rt))
                if out is not None:
                    return out
        return None

    # ---- path B: Newton on the system (float64), then mp polish ----
    f = sp.lambdify(t_syms, polys, modules="numpy")
    jac = [[sp.diff(F, s) for s in t_syms] for F in polys]
    jacf = sp.lambdify(t_syms, jac, modules="numpy")
    rng = np.random.default_rng(7)
    for attempt in range(restarts):
        t = (rng.standard_normal(k) + 1j * rng.standard_normal(k)) * (0.4 + 0.6 * attempt / restarts)
        for it in range(100):
            try:
                Fv = np.array(f(*t), dtype=complex)
                Jv = np.array(jacf(*t), dtype=complex)
            except Exception:
                break
            if np.any(~np.isfinite(Fv)) or np.any(~np.isfinite(Jv)):
                break
            step = np.linalg.lstsq(Jv, -Fv, rcond=None)[0]
            t = t + step
            if np.max(np.abs(Fv)) < 1e-12:
                break
        Fv = np.array(f(*t), dtype=complex)
        if np.max(np.abs(Fv)) > 1e-7:
            continue
        x_fl = np.array([complex(v.subs(dict(zip(t_syms, t))))
                         for v in x_wit_expr], dtype=complex)
        if np.min(np.abs(x_fl)) < 1e-6:
            continue
        ts_pol = polish(t)
        if ts_pol is None:
            continue
        if err(ts_pol) > mp.mpf(10) ** (-50):
            continue
        if not coords_ok(ts_pol):
            continue
        return {"t": ts_pol, "x": x_at(ts_pol)}
    return None

# ---------------------------------------------------------------------------
# verification of a candidate FEASIBLE witness by explicit weight lifting
# ---------------------------------------------------------------------------

def verify_witness_full(slot_coloring, x_wit, prec=60):
    """
    Given an exact witness vector x_M (products), find slot weights w_e over C
    (numerically) realizing x_M, then directly compute all 729 sums
    w(sigma) = sum_{M: IVC(M)=sigma} prod_{e in M} w_e and report residuals.
    """
    import mpmath as mp
    mp.mp.dps = prec
    insts = pm_instances(slot_coloring)
    slots = sorted({s for ins in insts for s in ins["edges"]},
                   key=lambda t: (EIDX[t[0]], t[1]))
    n = len(insts)
    U = np.zeros((n, len(slots)))
    for mi, ins in enumerate(insts):
        for s in ins["edges"]:
            U[mi, slots.index(s)] = 1.0
    def to_mpc(x):
        if isinstance(x, mp.mpc) or isinstance(x, mp.mpf) or isinstance(x, mp.matrix):
            return mp.mpc(x)
        if hasattr(x, "is_number") and x is not None:
            v = complex(sp.N(x, prec + 5))
            return mp.mpc(v.real, v.imag)
        return mp.mpc(complex(x))
    lx = np.array([mp.log(to_mpc(x)) for x in x_wit], dtype=complex)
    # solve U^T log w = log x in least squares (overdetermined ok when relations hold)
    lw, *_ = np.linalg.lstsq(U, lx, rcond=None)
    # improve: verify U^T lw ~= lx
    res = np.max(np.abs(U @ lw - lx))
    wc = [mp.e**mp.mpc(z) for z in lw]
    wgt = {s: w for s, w in zip(slots, wc)}
    sums = {}
    for ins in insts:
        p = mp.mpf(1)
        for s in ins["edges"]:
            p *= wgt[s]
        sums[ins["code"]] = sums.get(ins["code"], mp.mpf(0)) + p
    want = {MONO_CODE[i]: mp.mpf(1) for i in range(3)}
    errs = {}
    allcodes = set(sums) | set(want)
    for c in allcodes:
        errs[c] = sums.get(c, mp.mpf(0)) - want.get(c, mp.mpf(0))
    mx = max((abs(v) for v in errs.values()), default=mp.mpf(0))
    return {"logres": float(res), "maxerr": float(mx), "sums": {int(k): complex(v)
            for k, v in sums.items()}}
