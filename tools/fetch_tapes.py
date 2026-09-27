"""Download ladder episodes and keep only what a tape needs.

Reads a JSON list of episode ids, downloads each replay with the Kaggle CLI,
and writes replays/tapes/<episode>.json holding the seed, rewards, team names
and both seats' actions. The 30 MB replay is deleted afterwards.

    uv run python tools/fetch_tapes.py episodes.json
"""

import json
import os
import subprocess
import sys
import time

OUT = "replays/tapes"
TMP = "replays/tmp"


def compact(path):
    r = json.load(open(path))
    return dict(
        episode=r["info"]["EpisodeId"],
        seed=r["info"]["seed"],
        teams=r["info"]["TeamNames"],
        rewards=r["rewards"],
        actions=[[p["action"] for p in step] for step in r["steps"]],
    )


def main(ids):
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    for ep in ids:
        dst = f"{OUT}/{ep}.json"
        if os.path.exists(dst):
            continue
        for attempt in range(4):
            p = subprocess.run(["kaggle", "competitions", "replay", str(ep), "-p", TMP, "-q"],
                               capture_output=True, text=True)
            src = f"{TMP}/episode-{ep}-replay.json"
            if os.path.exists(src):
                json.dump(compact(src), open(dst, "w"))
                os.remove(src)
                print(ep, "ok", flush=True)
                break
            print(ep, "retry", (p.stdout + p.stderr)[-200:].strip(), flush=True)
            time.sleep(30 * (attempt + 1))
        time.sleep(1)


if __name__ == "__main__":
    main(json.load(open(sys.argv[1])))
