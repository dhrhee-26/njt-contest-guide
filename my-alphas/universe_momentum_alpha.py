"""
Cross-sectional momentum over the whole liquid universe — target_weight.

Showcases the contest's data tooling end to end:
  - **whole-universe panel load** — every symbol's close in one call
    (`Dataset.load("binance.klines.um.Close.1d")`), instead of concatenating
    one symbol at a time.
  - **liquidity gate** — `min_dollar_volume` drops thinly-traded coins so the
    cross-section is real (see ../rules.md §2.1). ~184 symbols clear $10M/day.
  - **the expanded universe** — any USDT-perp is fair game, not just the 9 majors.

The alpha itself: rank every liquid symbol by its LOOKBACK-day return, go long
the top quintile and short the bottom quintile, dollar-neutral, gross 1×.

Edit the line marked "← write your signal here". Run the whole file (Shift+Enter
in Jupyter, or `python universe_momentum_alpha.py`).

Needs the seed cache extracted (README §9) so the panel has data. For contest
W1 (target_weight, 1d).
"""
from __future__ import annotations

import pandas as pd

from feeds import Dataset
from framework.types import CleanData, Positions


# ─── Parameters (edit if needed) ──────────────────────────────────────────────
MIN_DOLLAR_VOLUME = 10_000_000     # liquidity floor (close × volume), rules §2.1
LOOKBACK          = 30             # momentum window, days
QUANTILE          = 0.2            # long top 20% / short bottom 20%


class Alpha:
    def get(self) -> tuple[Positions, CleanData]:
        # 1. Data — the whole liquid universe's daily close in one call.
        #    `min_dollar_volume` drops thin names; `holdout_recent=False` keeps
        #    the last 30 days (required for backtests).
        close = Dataset.load(
            "binance.klines.um.Close.1d",
            pandas=True, holdout_recent=False,
            min_dollar_volume=MIN_DOLLAR_VOLUME,
        )

        # 2. Signal — your alpha logic goes here.   ←  write your signal here
        #    Default: LOOKBACK-day return (cross-sectional momentum).
        signal = close.pct_change(LOOKBACK)

        # 3. Position — rank each day across symbols; long the top quintile,
        #    short the bottom, dollar-neutral and gross 1×. NaN (a coin not yet
        #    listed) is skipped by rank and ends up flat.
        rank = signal.rank(axis=1, pct=True)
        long = (rank >= 1 - QUANTILE).astype(float)
        short = (rank <= QUANTILE).astype(float)
        w_long = long.div(long.sum(axis=1), axis=0).fillna(0.0)
        w_short = short.div(short.sum(axis=1), axis=0).fillna(0.0)
        weights = 0.5 * w_long - 0.5 * w_short        # gross 1, dollar-neutral

        return Positions(weights=weights), CleanData(frames={"close": close})


# ─── Metadata — dash auto-registers via these ─────────────────────────────────
NAME        = "Universe momentum (30d, liquid)"
KIND        = "target_weight"
PRESET      = "binance_um_perpetual"                    # contest rule — do not change
DESCRIPTION = "Cross-sectional 30d momentum over all USDT-perps with >$10M/day; long top quintile, short bottom."


# ─── Copy-paste runner ────────────────────────────────────────────────────────
if __name__ == "__main__":
    from framework import evaluate_alpha
    from backtest import run_backtest, nav_fig

    bundle = evaluate_alpha({
        "alpha_cls": Alpha,
        "kind":      KIND,
        "name":      NAME,
        "preset":    PRESET,
    })
    res = run_backtest(bundle, start="2021-01-01", end=None)
    print(repr(res))
    print()
    print("Summary:")
    for k, v in res.summary().items():
        print(f"  {k:24s} {v}")
    nav_fig(res).show()


# ─── (Optional) Submit ────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     from framework import submit
#     submit(
#         Alpha(),
#         strategy_id="universe_momentum_v1",
#         name=NAME, preset=PRESET, description=DESCRIPTION,
#     )
