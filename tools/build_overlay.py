"""Append an overlay to a parent agent, with optional parameter overrides.

    uv run python tools/build_overlay.py main.py agents/overlays/clone_counter.py out.py '{"lead": 2}'

The overrides are written as `CC = {...}` just before the overlay, which reads them.
The overlay's last `def` becomes the file's last callable, so Kaggle runs it.
"""

import json
import sys


def main():
    parent, overlay, out = sys.argv[1:4]
    params = json.loads(sys.argv[4]) if len(sys.argv) > 4 else {}
    for key, value in params.items():
        if isinstance(value, list):
            params[key] = tuple(value)
    with open(parent) as f:
        src = f.read()
    with open(overlay) as f:
        block = f.read()
    with open(out, "w") as f:
        f.write(src.rstrip("\n") + f"\n\n\nCC = {params!r}\n" + block)


if __name__ == "__main__":
    main()
