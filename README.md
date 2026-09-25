# Kaggriculture agent

An `uv` project for building a Python agent for [Kaggle's Kaggriculture competition](https://www.kaggle.com/competitions/kaggriculture). A match has 720 turns; the agent with more banked coins at the end wins. See the [official environment guide](https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/kaggriculture/AGENTS.md) for actions and observations.

## Setup

```sh
uv sync
```

`uv` installs the pinned Python 3.12 environment and the local simulation and Kaggle CLI tools. Authenticate the Kaggle CLI separately before submitting; keep credentials outside this repository.

## Develop

Edit `main.py` and implement `agent(obs)`. Each call receives the current observation and returns actions for the farmer, hired hands, and market. `main.py` currently holds prvsiyan's public Apache-2.0 agent, [Kaggriculture Frontier | The Moon Counts Melons](https://www.kaggle.com/code/prvsiyan/kaggriculture-frontier-the-moon-counts-melons). Its license and notice are in `LICENSE` and `NOTICE.txt`. Our own earlier agents are frozen in `agents/`, and the public opponent pool is in `agents/public/` (see its README).

Run a complete local game against the built-in random agent:

```sh
uv run python scripts/smoke_test.py
```

Measure win rate against the public opponent pool:

```sh
uv run python tools/eval.py main.py agents/public/*.py -n 25 --seed0 9100 -j 11
```

Submit an archive that keeps the license and notice with the agent:

```sh
tar -czf submission.tar.gz main.py LICENSE NOTICE.txt
uv run kaggle competitions submit kaggriculture -f submission.tar.gz -m "Melons baseline"
```

The team shares one submission queue, and each new upload pushes out the older active submission. Check with your teammate before uploading.

Competition downloads, replays, logs, and local credentials are ignored by Git. Keep `uv.lock` committed so the local toolchain stays reproducible.
