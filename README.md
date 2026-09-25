# Kaggriculture agent

An `uv` project for building a Python agent for [Kaggle's Kaggriculture competition](https://www.kaggle.com/competitions/kaggriculture). A match has 720 turns; the agent with more banked coins at the end wins. See the [official environment guide](https://github.com/Kaggle/kaggle-environments/blob/master/kaggle_environments/envs/kaggriculture/AGENTS.md) for actions and observations.

## Setup

```sh
uv sync
```

`uv` installs the pinned Python 3.12 environment and the local simulation and Kaggle CLI tools. Authenticate the Kaggle CLI separately before submitting; keep credentials outside this repository.

## Develop

Edit `main.py` and implement `agent(obs)`. Each call receives the current observation and returns actions for the farmer, hired hands, and market. The included agent always passes; it verifies the entry point but will not earn income.

Run a complete local game against the built-in random agent:

```sh
uv run python scripts/smoke_test.py
```

Submit the single-file agent after joining the competition and configuring Kaggle authentication:

```sh
uv run kaggle competitions submit kaggriculture -f main.py -m "First agent"
```

Competition downloads, replays, logs, and local credentials are ignored by Git. Keep `uv.lock` committed so the local toolchain stays reproducible.
