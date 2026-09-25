# Public opponent pool

Frozen copies of public Kaggle agents, downloaded 2026-09-25 with `kaggle kernels output <ref>`. Use them as the **Opponent pool**:

```sh
uv run python tools/eval.py main.py agents/public/*.py -n 25 --seed0 9100 -j 11
```

`prvsiyan_melons.py` is the current **Champion** and the source of `main.py`. Its `LICENSE` and `NOTICE.txt` are at the repository root.

| File | Kaggle notebook | License | SHA-256 (first 12) |
| --- | --- | --- | --- |
| `prvsiyan_melons.py` | prvsiyan/kaggriculture-frontier-the-moon-counts-melons | Apache-2.0 | `178ae0f72764` |
| `ahmed_v55.py` | ahmedberatozer/kaggriculture-v55-one-turn-market-race-edge | Apache-2.0 | `f09034624844` |
| `ahmed_v48.py` | ahmedberatozer/kaggriculture-v48-clear-the-queue | Apache-2.0 | `4b5402888fee` |
| `tetsutani_demand.py` | tetsutani/demand-preserving-turn-sale-timing | Apache-2.0 | `127ed3e62988` |
| `farm2945.py` | thomastschinkel/the-2945-farm-96-vs-the-top-10-public-bots | Apache-2.0 | `bfee70e9daae` |
| `metav4_v13.py` | thomastschinkel/the-metav4-farm-submission-v13 | Apache-2.0 | `9d63494603f8` |
| `aurax7_v5.py` | aurax7/kaggriculture-shop-router-reactive-v5 | Apache-2.0 | `ea4c28e64d77` |
| `boatlee_v16rc5.py` | boatlee/v16-rc5-high-score-8c-4s-premium-market-lead | none stated | `f029fa0cb66a` |
| `kaito_v27.py` | kaitofukami/25-27-strict-future-v27-midgame-meta-reset | none stated | `f48c21166eac` |
| `kaito_v48.py` | kaitofukami/40-40-early-floor-39-46-top-10-v48-fast-routes | none stated | `dadee25a9840` |
| `ahmed_v57.py` | ahmedberatozer/kaggriculture-v57-funding-order-invariant (decoded from the notebook source) | Apache-2.0 | `2ee689fdc58f` |
| `haideptry_2965hybrid.py` | haideptry/the-2965-master-hybrid-engine (decoded from the notebook source) | Apache-2.0 | `cda529cb6b35` |
| `shiiin9_orderbook.py` | shiiin9/your-market-list-is-an-order-book | Apache-2.0 | `a16e0e9b40c4` |
| `haodou_ledger_v68.py` | haodou092/kaggriculture-harvest-ledger | Apache-2.0 | `3b5436114489` |
| `rayk_c95.py` | raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta (C95) | none stated | `489f5d197527` |

The four files without a stated license are git-ignored. They are for local evaluation only and must not be redistributed. `prvsiyan/kaggriculture-frontier-the-soil-remembers-rain` has a byte-identical `main.py` to Melons, and `abhinav0370/cha22-agent` has a byte-identical `main.py` to `tetsutani_demand.py`, so neither is listed separately. Ahmed V38 had no downloadable output. `yhay81/six-day-public-state-fieldbook` ships a Linux-only `agent.so`, so it cannot run on macOS.

**Entry points.** Kaggle runs the *last callable* defined in `main.py`, not `agent`. Before 2026-09-25 `tools/eval.py` imported `agent`, which made it run a stale inner bot for V48, V55, both Kaito agents and tetsutani. The loader now uses `kaggle_environments.agent.get_last_callable`. The baseline table below was measured with the old loader.

## Baseline, 2026-09-25 (old loader, superseded)

kaggle-environments 1.32.7, seeds 9100–9124, both seats, 50 matches per opponent. The table shows win %.

| Opponent | Melons | V55 |
| --- | ---: | ---: |
| prvsiyan Melons | mirror 50 | 2 |
| Ahmed V55 | 98 | mirror 50 |
| tetsutani demand | 94 | 38 |
| Metav4 v13 | 98 | 86 |
| 2945 Farm | 86 | 90 |
| Ahmed V48, aurax7 v5, boatlee V16-RC5, Kaito v27, Kaito v48 | 100 | 100 |

The top agents each bank about 97k per match, and margins between them are only 1–3k.

## Melons with the corrected loader, 2026-09-25

Same seeds and settings, rerun only for the five opponents whose entry point changed.

| Opponent | Melons win % | Melons bank | Opponent bank |
| --- | ---: | ---: | ---: |
| Ahmed V48 | 100 | 99,237 | 94,605 |
| Ahmed V55 | 98 | 97,785 | 96,530 |
| Kaito v27 | 100 | 114,785 | 84,230 |
| Kaito v48 | 100 | 108,137 | 79,287 |
| tetsutani demand | **6** | 96,666 | 98,339 |
