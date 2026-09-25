# Kaggriculture

Two farms compete over a 30-day season. They trade on one shared market, and the farm with more coins banked at the end wins.

## Language

### Competition

**Match**:
One 720-step game between two agents on a single seed. It ends in a win, a loss, or a draw.
_Avoid_: game, episode (use these only when quoting Kaggle tooling)

**Win rate**:
The share of matches an agent wins against an **Opponent pool**, counted over many seeds with the agent playing both seats. This is the objective every design choice is judged by.
_Avoid_: score, reward (these mean the coin total of a single match)

**Opponent pool**:
The fixed set of agents a candidate is evaluated against. It always includes a **Mirror**.

**Mirror**:
A match between an agent and a copy of itself. It is the closest stand-in for a strong ladder opponent, because both farms compete for the same market.

**Champion**:
The frozen agent version that currently scores best. A frozen version is never edited.

**Candidate**:
The agent version under development. It becomes the **Champion** only after beating the current **Champion** by a clear margin in **Win rate**, without falling behind against the rest of the **Opponent pool**.

### Economy

**Shared market**:
The market inventory that both farms buy from and sell to. One farm's trades move the prices the other farm sees.

**Sink**:
A product whose price barely falls however much is sold (egg, wheat). Income from a sink is limited by how much you can produce, not by the market.

**Finite pool**:
A product whose price reaches the $1 floor after a limited number of units, so the market holds a fixed amount of money for it that both farms share (melon, fertilizer, tomato, carrot, wool, milk, strawberry). The farm that sells first takes most of the money.
_Avoid_: premium good (that term is about the base price, not about how much the market can absorb)

**Fertilizer pool**:
The **Finite pool** for fertilizer. Nothing refills it; the only thing that ever moves its price back up is someone buying fertilizer.

**Opponent forecast**:
Our estimate, built from the opponent's visible farm, of how many units the opponent will bring to each **Finite pool** and on which day. The opponent's shed is hidden, so the forecast only covers what is visible growing or living on the farm.

**Melon wave**:
A batch of melons planted on the same day and harvested together about 10 days later, when they are sold into the melon **Finite pool**. Several small waves take more of the pool than one large wave, because each wave uses less of the farm's early cash.

**Care bonus**:
The extra egg a goose lays after a day on which it was both fed and cared for. It is paid only if the goose is also fed on the day of the next lay. A goose lays its base egg and produces fertilizer even when unfed, so feeding pays only for the bonus and for preventing an **Escape**.

**Payback test**:
The check a purchase (a goose, a quadrant of land) must pass: at today's prices, and counting the hand labour it needs, it has to earn back its price before the season ends. Labour cost rises steeply with each extra hand, so late or large expansions usually fail this test.

**Escape**:
The permanent loss of an animal that went unfed for two days in a row.

## Relationships

- **Win rate** is measured over **Matches** against an **Opponent pool**
- Every **Opponent pool** contains at least one **Mirror**
- A **Candidate** is compared against the **Champion**, and there is exactly one **Champion** at a time

## Flagged ambiguities

- "Winning" meant both "top of the leaderboard" and "most coins". Resolved: we optimize **Win rate**, and the coin total only matters relative to the opponent's.
