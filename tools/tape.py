"""Tape opponents: replay one seat of a downloaded Kaggle episode.

A tape agent returns, turn by turn, the actions a ladder agent actually took
in a recorded episode. Played on that episode's seed, it stands in for an
agent we cannot download. Replaying both seats reproduces the ladder rewards
exactly, and so does our own agent against the other seat's tape. A tape does
not react to us, so its market orders fill at different prices than they did
on the ladder.

Top agents spend down to a few coins, so a price a few coins higher makes one
recorded purchase fail (or a failed one succeed) and every later action goes
out of sync. To keep the tape on its recorded course, the recorded game is
replayed first and every unit the tape managed to buy, sell or hire is
counted per turn. In the live game the tape gets exactly those units: extra
ones are refused, and one it cannot afford is paid with a loan. `play`
reports the tape's score net of those loans.

Tapes come from tools/fetch_tapes.py (replays/tapes/<episode>.json). A tape
list is a JSON list of [episode, seat, ...] rows naming the seat to replay.

    uv run python tools/tape.py check replays/tapes/123.json
    uv run python tools/tape.py eval main.py logs/cand/h48.py --tapes replays/tapes_top.json -j 11
"""

import argparse
import collections
import json
import os
import statistics
from multiprocessing import Pool

import kaggle_environments.envs.kaggriculture.kaggriculture as K
from kaggle_environments import make
from kaggle_environments.agent import get_last_callable

TAPES = "replays/tapes"
PASS = {"farmer": ["PASS"], "hands": [], "market": []}


def load_tape(episode):
    with open(f"{TAPES}/{episode}.json") as f:
        return json.load(f)


# The live game's farms, the seat that is a tape, the loans paid to it, and the
# units it traded per (step, op, item) in the recorded game.
STATE = dict(farms=[], step=0, tape_seat=None, loans=0.0, mode=None, script=collections.Counter())
_INTERPRETER = K.interpreter


def _is_tape(farm):
    seat = STATE["tape_seat"]
    return seat is not None and seat < len(STATE["farms"]) and STATE["farms"][seat] is farm


def _scripted(farm, key, cost, do, done):
    """Run one tape trade `do()`: counted when recording, held to the recorded count when following."""
    if not _is_tape(farm) or STATE["mode"] is None:
        return do()
    key = (STATE["step"],) + key
    if STATE["mode"] == "record":
        out = do()
        if done(out):
            STATE["script"][key] += 1
        return out
    if STATE["script"][key] <= 0:
        return False
    if cost and farm["money"] < cost:
        STATE["loans"] += cost - farm["money"]
        farm["money"] = cost
    out = do()
    if done(out):
        STATE["script"][key] -= 1
    return out


def _install():
    if getattr(K, "_tape_installed", False):
        return
    commit, hire, land = K._commit_unit, K._do_hire, K._do_buy_land

    def c(op, item, price, farm, private, market, cap=100):
        return _scripted(farm, (op, item), 0 if op == "SELL" else price,
                         lambda: commit(op, item, price, farm, private, market, cap), bool)

    def h(farm, private, board_size, *a, **k):
        n = len(farm["hands"])
        return _scripted(farm, ("HIRE",), K._hire_cost(farm["hires_today"], *a, **k),
                         lambda: hire(farm, private, board_size, *a, **k), lambda _: len(farm["hands"]) > n)

    def l(farm, board_size):
        n = len(farm["unlocked_quadrants"])
        cost = K.LAND_PRICES[n - 1] if n - 1 < len(K.LAND_PRICES) else 0
        return _scripted(farm, ("LAND",), cost, lambda: land(farm, board_size),
                         lambda _: len(farm["unlocked_quadrants"]) > n)

    K._commit_unit, K._do_hire, K._do_buy_land = c, h, l
    K._tape_installed = True


def track(state, env):
    obs = state[0].observation
    if obs.get("farms"):
        STATE["farms"][:] = list(obs["farms"])
    STATE["step"] = obs.get("step", 0)
    return _INTERPRETER(state, env)


def new_env(seed, tape_seat=None, mode=None):
    """An environment that records (mode "record") or enforces (mode "follow") the `tape_seat` farm's trades."""
    _install()
    if mode == "record":
        STATE["script"] = collections.Counter()
    STATE.update(farms=[], step=0, tape_seat=tape_seat, loans=0.0, mode=mode)
    env = make("kaggriculture", configuration={"seed": seed})
    env.interpreter = track
    return env


def record(tape, seat):
    """Replay the recorded game so the live game can hold `seat`'s tape to its recorded trades."""
    env = new_env(tape["seed"], seat, "record")
    env.run([tape_agent(tape, 0), tape_agent(tape, 1)])
    return env


def tape_agent(tape, seat):
    """Agent that plays `seat`'s recorded actions. At step s it returns the action recorded at s+1."""
    actions = tape["actions"]

    def agent(obs, config=None):
        s = obs["step"] + 1
        return actions[s][seat] if s < len(actions) else PASS

    return agent


def load_agent(path):
    with open(path) as f:
        return get_last_callable(f.read(), path=path)


def play(args):
    """Candidate `path` takes the seat opposite the tape's `seat`.

    Returns (episode, mine, theirs net of loans, loans)."""
    path, episode, seat = args
    tape = load_tape(episode)
    agents = [None, None]
    agents[seat] = tape_agent(tape, seat)
    agents[1 - seat] = load_agent(path)
    record(tape, seat)
    env = new_env(tape["seed"], seat, "follow")
    env.run(agents)
    last = env.steps[-1]
    return episode, last[1 - seat].reward, last[seat].reward - STATE["loans"], STATE["loans"]


def check(paths):
    for p in paths:
        tape = json.load(open(p))
        env = new_env(tape["seed"])
        env.run([tape_agent(tape, 0), tape_agent(tape, 1)])
        print(p, "recorded", tape["rewards"], "replayed", [s.reward for s in env.steps[-1]])


def evaluate(agents, rows, jobs):
    rows = [r for r in rows if os.path.exists(f"{TAPES}/{r[0]}.json")]
    # What the real ladder opponent in the other seat scored against the tape.
    recorded = {(r[0], r[1]): load_tape(r[0])["rewards"] for r in rows}
    print(f"{'agent':28} {'tapes':>5} {'win%':>6} {'mean margin':>12} {'median':>8} {'mine':>8} {'tape':>8} {'loans':>6}")
    ref = [recorded[(r[0], r[1])][1 - r[1]] - recorded[(r[0], r[1])][r[1]] for r in rows]
    wins = sum(m > 0 for m in ref) + 0.5 * sum(m == 0 for m in ref)
    print(f"{'(recorded ladder opponent)':28} {len(rows):5} {100 * wins / len(rows):6.1f} {statistics.mean(ref):12.0f} "
          f"{statistics.median(ref):8.0f}")
    results = {}
    with Pool(jobs) as pool:
        for path in agents:
            out = pool.map(play, [(path, r[0], r[1]) for r in rows])
            m = [a - b for _, a, b, _ in out]
            wins = sum(x > 0 for x in m) + 0.5 * sum(x == 0 for x in m)
            print(f"{os.path.basename(path):28} {len(m):5} {100 * wins / len(m):6.1f} {statistics.mean(m):12.0f} "
                  f"{statistics.median(m):8.0f} {statistics.mean(o[1] for o in out):8.0f} "
                  f"{statistics.mean(o[2] for o in out):8.0f} {statistics.mean(o[3] for o in out):6.0f}", flush=True)
            results[path] = [[r[0], r[1], o[1], o[2], o[3]] for r, o in zip(rows, out)]
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["check", "eval"])
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--tapes", default="replays/tapes_top.json")
    ap.add_argument("-j", type=int, default=11)
    ap.add_argument("--out", help="write per-tape results as JSON")
    a = ap.parse_args()
    if a.cmd == "check":
        check(a.paths)
    else:
        res = evaluate(a.paths, json.load(open(a.tapes)), a.j)
        if a.out:
            json.dump(res, open(a.out, "w"))


if __name__ == "__main__":
    main()
