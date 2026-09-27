"""Embed a route library into the leader prototype to make a self-contained agent.

    uv run python tools/build_submission.py proto/leader.py replays/library_BOEY.json out.py
"""

import base64
import json
import sys
import zlib


def main(template, library, out):
    lib = json.load(open(library))
    table, index = [], {}
    routes = []
    for e in lib:
        ids = []
        for a in e["actions"]:
            a = a if isinstance(a, dict) else {"farmer": ["PASS"], "hands": [], "market": []}
            k = json.dumps(a, separators=(",", ":"), sort_keys=True)
            if k not in index:
                index[k] = len(table)
                table.append(a)
            ids.append(index[k])
        routes.append(ids)
    land = []
    for e in lib:
        changes, prev = [], 0
        for t, o in enumerate(e["own"]):
            if o[0] != prev:
                changes.append([t, o[0]])
                prev = o[0]
        land.append(changes)
    blob = json.dumps({"a": table, "r": routes, "s": [e["shops"] for e in lib],
                       "w": [e["reward"] for e in lib], "q": land}, separators=(",", ":"))
    enc = base64.b85encode(zlib.compress(blob.encode(), 9)).decode()
    src = open(template).read()
    marker = "_LIB_BLOB = None"
    assert src.count(marker) == 1
    src = src.replace(marker, "_LIB_BLOB = " + repr(enc))
    open(out, "w").write(src)
    print(out, len(lib), "routes", len(table), "actions", round(len(src) / 1e6, 2), "MB")


if __name__ == "__main__":
    main(*sys.argv[1:4])
