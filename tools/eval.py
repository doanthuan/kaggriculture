"""Win-rate evaluation of a Candidate against an Opponent pool.

    uv run python tools/eval.py main.py agents/v5.py starter -n 50

Each opponent plays n seeds (from --seed0) in both seats. Draws count 0.5.
Agents are loaded fresh per match so module-level state is never shared.
"""

import argparse
import importlib.util
import math
import os
import statistics
import uuid
from concurrent.futures import ProcessPoolExecutor

BUILTIN = {"starter", "random"}


def load(path):
    if path in BUILTIN:
        return path
    spec = importlib.util.spec_from_file_location("a_" + uuid.uuid4().hex, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.agent


def play(job):
    cand, opp, seed, seat = job
    from kaggle_environments import make

    agents = [load(cand), load(opp)]
    if seat == 1:
        agents.reverse()
    env = make("kaggriculture", configuration={"seed": seed})
    env.run(agents)
    last = env.steps[-1]
    me, them = last[seat], last[1 - seat]
    ok = me.status == "DONE"
    r_me, r_them = (me.reward or 0), (them.reward or 0)
    score = 1.0 if r_me > r_them else 0.5 if r_me == r_them else 0.0
    return opp, seed, seat, score if ok else 0.0, r_me, r_them, me.status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("candidate")
    ap.add_argument("opponents", nargs="+")
    ap.add_argument("-n", type=int, default=50, help="seeds per opponent")
    ap.add_argument("--seed0", type=int, default=1000)
    ap.add_argument("-j", type=int, default=10)
    a = ap.parse_args()

    jobs = [(a.candidate, o, a.seed0 + s, seat)
            for o in a.opponents for s in range(a.n) for seat in (0, 1)]
    res = {o: [] for o in a.opponents}
    with ProcessPoolExecutor(a.j) as ex:
        for opp, seed, seat, sc, rm, rt, st in ex.map(play, jobs, chunksize=2):
            res[opp].append((sc, rm, rt))
            if st != "DONE":
                print(f"!! {opp} seed={seed} seat={seat} status={st}")

    print(f"{'opponent':28s} {'games':>5s} {'win%':>6s} {'±2se':>5s} {'mine':>8s} {'theirs':>8s}")
    for o, rs in res.items():
        k = len(rs)
        p = sum(r[0] for r in rs) / k
        se2 = 2 * math.sqrt(max(p * (1 - p), 1e-9) / k) * 100
        print(f"{os.path.basename(o):28s} {k:5d} {p * 100:6.1f} {se2:5.1f} "
              f"{statistics.mean(r[1] for r in rs):8.0f} {statistics.mean(r[2] for r in rs):8.0f}")


if __name__ == "__main__":
    main()
