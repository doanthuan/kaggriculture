"""Evaluate parameter variants of an agent against an opponent pool.

    uv run python tools/sweep.py main.py '{"melon_n": 20}' '{"melon_n": 30}' --vs agents/v6.py -n 25

Each variant is written to a temp file with P.update(<json>) appended, then run through eval.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("agent")
    ap.add_argument("variants", nargs="+", help="JSON dicts of P overrides")
    ap.add_argument("--vs", nargs="+", default=["agents/v6.py"])
    ap.add_argument("-n", type=int, default=25)
    ap.add_argument("--seed0", type=int, default=1000)
    a = ap.parse_args()
    src = open(a.agent).read()
    tmp = tempfile.mkdtemp(prefix="sweep_")
    for i, v in enumerate(a.variants):
        over = json.loads(v)
        for k, val in over.items():
            if isinstance(val, list):
                over[k] = tuple(val)
        path = os.path.join(tmp, f"variant{i}.py")
        with open(path, "w") as f:
            f.write(src + f"\nP.update({over!r})\n")
        print(f"\n### {v}", flush=True)
        out = subprocess.run([sys.executable, "tools/eval.py", path, *a.vs, "-n", str(a.n), "--seed0", str(a.seed0)],
                             capture_output=True, text=True)
        print("\n".join(out.stdout.strip().splitlines()[1:]) or out.stderr[-2000:], flush=True)


if __name__ == "__main__":
    main()
