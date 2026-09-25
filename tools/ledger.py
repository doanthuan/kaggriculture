"""Money ledger per player: where each agent's coins came from and went.

    uv run python tools/ledger.py main.py agents/v5.py -n 10
"""

import argparse
import collections

import kaggle_environments.envs.kaggriculture.kaggriculture as K
from kaggle_environments import make
from kaggle_environments.agent import get_last_callable

KEYS = ["SELL_EGG", "SELL_FERTILIZER", "SELL_WHEAT", "BUY_PRODUCT_WHEAT", "BUY_PRODUCT_FERTILIZER",
        "BUY_ANIMAL_GOOSE", "BUY_SEED_WHEAT", "HIRE", "LAND"]


def load(path):
    """Load an agent the way the Kaggle runner does: the last callable in the file."""
    if path in ("starter", "random"):
        return path
    with open(path) as f:
        return get_last_callable(f.read(), path=path)


LED = [collections.Counter(), collections.Counter()]
FARMS = []


def who(farm):
    for i, f in enumerate(FARMS):
        if f is farm:
            return i
    return None


def patch():
    commit, hire, land = K._commit_unit, K._do_hire, K._do_buy_land

    def c(op, item, price, farm, private, market, cap=100):
        ok = commit(op, item, price, farm, private, market, cap)
        i = who(farm)
        if ok and i is not None:
            LED[i][f"{op}_{item}"] += price if op == "SELL" else -price
        return ok

    def h(farm, *a, **k):
        before = farm["money"]
        hire(farm, *a, **k)
        i = who(farm)
        if i is not None:
            LED[i]["HIRE"] -= before - farm["money"]

    def l(farm, *a, **k):
        before = farm["money"]
        land(farm, *a, **k)
        i = who(farm)
        if i is not None:
            LED[i]["LAND"] -= before - farm["money"]

    K._commit_unit, K._do_hire, K._do_buy_land = c, h, l
    interp = K.interpreter

    def track(state, env):
        farms = state[0].observation.get("farms") if hasattr(state[0].observation, "get") else None
        if farms:
            FARMS[:] = list(farms)
        return interp(state, env)

    return track


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("-n", type=int, default=10)
    ap.add_argument("--seed0", type=int, default=1000)
    args = ap.parse_args()
    track = patch()
    tot = [collections.Counter(), collections.Counter()]
    finals = [[], []]
    for s in range(args.n):
        for L in LED:
            L.clear()
        env = make("kaggriculture", configuration={"seed": args.seed0 + s})
        env.interpreter = track
        env.run([load(args.a), load(args.b)])
        last = env.steps[-1]
        geese = [sum(1 for r in f["tiles"] for t in r if isinstance(t, dict) and "animal" in t)
                 for f in last[0].observation.farms]
        print(f"seed {args.seed0 + s}: final={[st.reward for st in last]} geese_end={geese}")
        for i in (0, 1):
            tot[i].update(LED[i])
            finals[i].append(last[i].reward)
    print(f"\nmean per match over {args.n} seeds")
    print(f"{'':24s} {'A':>9s} {'B':>9s}")
    for k in KEYS + sorted(set(tot[0]) | set(tot[1]) - set(KEYS)):
        print(f"{k:24s} {tot[0][k] / args.n:9.0f} {tot[1][k] / args.n:9.0f}")
    print(f"{'FINAL':24s} {sum(finals[0]) / args.n:9.0f} {sum(finals[1]) / args.n:9.0f}")


if __name__ == "__main__":
    main()
