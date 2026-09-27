"""Where the money goes: our agent vs top ladder agents, per product and phase.

For every tape it plays two games on the tape's seed:
  top    the recorded episode (both seats replayed), ledger of the top agent
  us     our agent against the top agent's tape, ledger of both seats
and prints the mean income and spending per product, split into days 0-10,
11-20 and 21-29, plus what was left in the shed at the end.

    uv run python tools/tape_ledger.py main.py --tapes replays/tapes_top.json -j 11
"""

import argparse
import collections
import json
import os
from multiprocessing import Pool

import kaggle_environments.envs.kaggriculture.kaggriculture as K

import tape as T
from tape import TAPES, load_agent, load_tape, tape_agent

LED = [collections.Counter(), collections.Counter()]


def phase():
    d = T.STATE["step"] // 24
    return "d00-10" if d <= 10 else "d11-20" if d <= 20 else "d21-29"


def who(farm):
    for i, f in enumerate(T.STATE["farms"]):
        if f is farm:
            return i
    return None


def patch():
    T._install()
    commit, hire, land = K._commit_unit, K._do_hire, K._do_buy_land

    def c(op, item, price, farm, private, market, cap=100):
        ok = commit(op, item, price, farm, private, market, cap)
        i = who(farm)
        if ok and i is not None:
            LED[i][(f"{op}_{item}", phase())] += price if op == "SELL" else -price
            LED[i][(f"n_{op}_{item}", phase())] += 1
        return ok

    def h(farm, *a, **k):
        before = farm["money"]
        hire(farm, *a, **k)
        i = who(farm)
        if i is not None:
            LED[i][("HIRE", phase())] -= before - farm["money"]

    def l(farm, *a, **k):
        before = farm["money"]
        land(farm, *a, **k)
        i = who(farm)
        if i is not None:
            LED[i][("LAND", phase())] -= before - farm["money"]

    K._commit_unit, K._do_hire, K._do_buy_land = c, h, l


def summarize(env):
    last = env.steps[-1]
    out = []
    for i in (0, 1):
        led = collections.Counter({f"{k[0]}|{k[1]}": v for k, v in LED[i].items()})
        for item, n in last[i].observation["private"]["shed"].items():
            if n:
                led[f"LEFT_{item}|end"] += n
        led["FINAL|end"] = last[i].reward
        out.append(led)
    for L in LED:
        L.clear()
    return out


def job(args):
    path, episode, seat = args
    if not getattr(K, "_ledger_installed", False):
        patch()
        K._ledger_installed = True
    tape = load_tape(episode)
    for L in LED:
        L.clear()
    top = summarize(T.record(tape, seat))[seat]
    agents = [None, None]
    agents[seat] = tape_agent(tape, seat)
    agents[1 - seat] = load_agent(path)
    env = T.new_env(tape["seed"], seat, "follow")
    env.run(agents)
    g = summarize(env)
    g[seat]["LOANS|end"] = T.STATE["loans"]
    return top, g[1 - seat], g[seat]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agent")
    ap.add_argument("--tapes", default="replays/tapes_top.json")
    ap.add_argument("-j", type=int, default=11)
    ap.add_argument("--only", default="", help="comma list of key prefixes to show")
    a = ap.parse_args()
    rows = [r for r in json.load(open(a.tapes)) if os.path.exists(f"{TAPES}/{r[0]}.json")]
    with Pool(a.j) as pool:
        out = pool.map(job, [(a.agent, r[0], r[1]) for r in rows])
    n = len(out)
    tot = [collections.Counter() for _ in range(3)]
    for triple in out:
        for t, led in zip(tot, triple):
            t.update(led)
    keys = sorted(set().union(*tot), key=lambda k: (k.split("|")[0].lstrip("n_"), k))
    print(f"{n} tapes. top = top agent in its recorded game; us = {a.agent} vs tape; tape = tape vs us")
    print(f"{'key':34} {'top':>9} {'us':>9} {'tape':>9} {'us-top':>9}")
    for k in keys:
        if a.only and not any(k.startswith(p) for p in a.only.split(",")):
            continue
        v = [t[k] / n for t in tot]
        if max(abs(x) for x in v) < 1:
            continue
        print(f"{k:34} {v[0]:9.0f} {v[1]:9.0f} {v[2]:9.0f} {v[1] - v[0]:9.0f}")


if __name__ == "__main__":
    main()
