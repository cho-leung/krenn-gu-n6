"""run_struct_engine.py -- solve the all-pairs K=2 structural problem with a
given pysat engine; report SAT/UNSAT with the decoded slot coloring (P1 and
brute checks).  Usage: python3 run_struct_engine.py <engine> <outfile>
"""
import sys, time, json
from pysat.solvers import Solver
from mq_struct import StructSolver
from mq_struct_selftest import brute_pass

def main():
    engine, out = sys.argv[1], sys.argv[2]
    mono = (0, 4, 8)
    s = StructSolver(2, *mono, extra_on_forced=True)
    s.build()
    t0 = time.time()
    S = Solver(name=engine, bootstrap_with=s.alloc)
    sat = S.solve()
    res = {"engine": engine, "sat": sat, "secs": round(time.time() - t0, 2)}
    if sat:
        model = S.get_model()
        assert s.check_model(model), "model violates CNF"
        sc = s.model_to_slot_coloring(model)
        p1 = all(len(set(lst)) == len(lst) for lst in sc.values())
        bp = brute_pass(sc, mono)
        res["p1"] = p1
        res["brute_pass"] = bp
        res["coloring"] = {str(k): [list(c) for c in v] for k, v in sc.items()}
    S.delete()
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res)[:2000])

if __name__ == "__main__":
    main()
