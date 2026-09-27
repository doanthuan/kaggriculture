# Leader routes

`leader.py` replays a top team's recorded ladder games as route plans. It keeps tetsutani's generic `Chassis` and `make_agent` from `main.py` and drops tetsutani's own routes and layers. In their place it adds:

- **Router.** Follows the library game whose shop sequence matches the shops the town has unlocked so far. When a new shop breaks the match, it switches to the matching game whose purchases so far agree most with ours.
- **Land catch-up.** Buys land the followed game owned by now but we missed, once we can pay for it.
- **Feeding helper.** From hour 10, hires one extra hand to feed animals that would escape tonight.
- **End-of-game sell-off.** The chassis's own sell-off at the last turn, switched on.

Submitted as ref 56613129 (v7b) with the library of the team Boey.

## Pipeline

Replays, tapes and libraries live in `replays/`, which Git ignores.

1. `tools/fetch_tapes.py ids.json` downloads episodes with `kaggle competitions replay` and keeps only the seed, rewards and both seats' actions.
2. `tools/build_library.py replays/library_index.json` replays each leader episode. It writes `replays/library_<family>.json` with the actions, the shop sequence and per-step snapshots of what the leader owned. The index lists episode, seat, submission and family for each leader game, taken from the `ListEpisodes` lists of that team's submissions.
3. `tools/build_submission.py proto/leader.py replays/library_BOEY.json out.py` embeds the library to make one self-contained agent (about 6.6 MB).
4. Evaluate with `tools/tape.py eval` (top-agent tapes) and `tools/eval.py` (public pool).

A library must never include the episodes used as evaluation tapes. `library_index.json` excludes every episode in `replays/tapes_top.json`.

## Findings

These are the results on 184 top-agent tapes. For reference, the real 2600+ opponents in those games won 44.0%.

| variant | win% | mean margin | public pool (main.py / Ledger V68 / 2965 hybrid / Melons) |
|---|---|---|---|
| main.py (h48) | 35.3 | −3.0k | — |
| v1: router only, 238 Boey games | 44.6 | −3.6k | — |
| v4: + land catch-up, feed-and-place helper, sell-off | 48.4 | +1.0k | 50 / 35 / 35 / 35 |
| **v7b: v4 with a feeding-only helper** | **52.7** | **+1.8k** | **55 / 55 / 55 / 55** |

What didn't work:

- **Switching to the nearest-state game every day:** 27%.
- **Re-buying animals, seeds and hires the leader had:** worse.
- **Placing animals left in the shed:** worse. Leaders sometimes keep animals there on purpose.
- **Moving or adding the leader's market orders:** worse. Their order sequences are finely timed.
- **Mixing families in one library:** 27%.
- **The DSM library:** 17%. DSM runs so short of cash that its plans fall apart once ours differs.

Tapes cannot react to us, so a tape win rate overstates strength against the real, reactive agents.
