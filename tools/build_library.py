"""Build a route library from downloaded leader episodes.

Each library entry is one leader seat of one ladder episode: its 720 recorded
actions and the shop sequence the town unlocked in that game. The shop draw
shares its RNG with the day's weed spawns, whose number of draws depends on
both farms, so the sequence is taken from a full replay of the episode rather
than from the seed.

    uv run python tools/build_library.py replays/library_index.json -j 10
"""

import json
import os
import sys
from multiprocessing import Pool

from tape import TAPES, load_tape, new_env, tape_agent

ANIMALS = ("GOOSE", "COW", "SHEEP")
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")


_CROP_CH = {"WHEAT": "w", "CARROT": "c", "TOMATO": "t", "STRAWBERRY": "s", "MELON": "m"}
_ANIMAL_CH = {"GOOSE": "G", "COW": "C", "SHEEP": "S"}


def tile_string(tiles):
    """One character per tile: . empty, # locked, x weed, crop letter, animal letter, o/p empty coop/pasture."""
    out = []
    for row in tiles:
        for t in row:
            if t is None:
                out.append(".")
            elif t == "LOCKED":
                out.append("#")
            elif isinstance(t, dict) and t.get("kind") == "WEED":
                out.append("x")
            elif isinstance(t, dict) and t.get("animal"):
                out.append(_ANIMAL_CH.get(t["animal"], "?"))
            elif isinstance(t, dict) and t.get("crop"):
                out.append(_CROP_CH.get(t["crop"], "?"))
            elif isinstance(t, dict) and t.get("kind") in ("COOP", "PASTURE"):
                out.append("o" if t["kind"] == "COOP" else "p")
            else:
                out.append("?")
    return "".join(out)


def extract(entry):
    path = f"{TAPES}/{entry['ep']}.json"
    if not os.path.exists(path):
        return None
    tape = load_tape(entry["ep"])
    env = new_env(tape["seed"])
    env.run([tape_agent(tape, 0), tape_agent(tape, 1)])
    last = env.steps[-1]
    seat = entry["seat"]
    rewards = [s.reward for s in last]
    if rewards != tape["rewards"]:
        return None
    # What the leader owned before its action at each step: extra quadrants,
    # animals per species (on tiles, in the shed or carried), seeds per crop,
    # and hired hands.
    own = []
    for st in env.steps[:720]:
        obs = st[seat].observation
        farm = obs["farms"][seat]
        priv = obs["private"]
        animals = {a: priv["shed"].get(a, 0) + sum(inv.get(a, 0) for inv in priv["inventories"]) for a in ANIMALS}
        for row in farm["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("animal") in animals:
                    animals[t["animal"]] += 1
        own.append([len(farm["unlocked_quadrants"]) - 1] + [animals[a] for a in ANIMALS]
                   + [priv["seeds"].get(c, 0) for c in CROPS] + [len(farm["hands"])])
    # Start-of-day snapshots for nearest-state route switching.
    days = []
    for d in range(30):
        obs = env.steps[d * 24][seat].observation
        farm = obs["farms"][seat]
        days.append(dict(money=farm["money"], tiles=tile_string(farm["tiles"]), own=own[d * 24],
                         shed={k: v for k, v in obs["private"]["shed"].items() if v}))
    return dict(ep=entry["ep"], seat=seat, own=own, days=days, sid=entry["sid"], fam=entry["fam"], seed=tape["seed"],
                reward=rewards[seat], opp_reward=rewards[1 - seat],
                shops=list(last[0].observation["town"]["unlocked_shops"]),
                actions=[tape["actions"][s + 1][seat] if s + 1 < len(tape["actions"]) else None
                         for s in range(720)])


def main():
    index = json.load(open(sys.argv[1]))
    jobs = int(sys.argv[sys.argv.index("-j") + 1]) if "-j" in sys.argv else 10
    with Pool(jobs) as pool:
        out = [e for e in pool.map(extract, index, chunksize=4) if e]
    fams = {}
    for e in out:
        fams.setdefault(e["fam"], []).append(e)
    for fam, entries in fams.items():
        json.dump(entries, open(f"replays/library_{fam}.json", "w"))
        print(fam, len(entries), "entries")
    print("skipped", len(index) - len(out))


if __name__ == "__main__":
    main()
