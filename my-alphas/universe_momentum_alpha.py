"""
Cross-sectional momentum over the whole liquid universe — margin_weight.

The weight-based example, end to end. Showcases everything the contest tooling
now does:
  - **whole-universe panel load** — every symbol's close in one call
    (`Dataset.load("binance.klines.um.Close.1d")`), instead of concatenating
    one symbol at a time.
  - **liquidity gate** — `min_dollar_volume` drops thinly-traded coins so the
    cross-section is real (see ../rules.md §2.1). ~184 symbols clear $10M/day.
  - **the expanded universe** — any USDT-perp is fair game, not just the 9 majors.
  - **margin_weight engine** — your weights are traded *statefully* on real
    cash/positions with a leverage cap, liquidation and funding. At 1× gross it
    reproduces the old vectorized target_weight exactly (no decomposition gap);
    above 1× you actually use leverage.
  - **executable order stream** — `emit_orders=True` surfaces the real BUY/SELL
    orders the engine places (timestamp/symbol/side/qty/price) — the same shape
    you'd send to the exchange. The backtest result and the live-trading order
    list come out of the *one* run.

The alpha itself: rank every liquid symbol by its LOOKBACK-day return, go long
the top quintile and short the bottom quintile, dollar-neutral, gross 1×.

Edit the line marked "← write your signal here". Run the whole file (Shift+Enter
in Jupyter, or `python universe_momentum_alpha.py`).

Needs the seed cache extracted (README §9) so the panel has data. margin_weight
is the default contest kind; set KIND = "target_weight" to use the old
vectorized engine instead.
"""
from __future__ import annotations

import pandas as pd

from feeds import Dataset
from framework.types import CleanData, MarginPositions


# ─── Parameters (edit if needed) ──────────────────────────────────────────────
MIN_DOLLAR_VOLUME = 10_000_000     # liquidity floor (close × volume), rules §2.1
LOOKBACK          = 30             # momentum window, days
QUANTILE          = 0.2            # long top 20% / short bottom 20%
MAX_LEVERAGE      = 3.0            # gross cap; this alpha runs at 1×, headroom unused
MARGIN_MODE       = "cross"        # "cross" | "isolated"


class Alpha:
    def get(self) -> tuple[MarginPositions, CleanData]:
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
        #    listed) is skipped by rank and ends up flat. Scale the 0.5s up to
        #    lever the book (gross stays under MAX_LEVERAGE or it's capped).
        rank = signal.rank(axis=1, pct=True)
        long = (rank >= 1 - QUANTILE).astype(float)
        short = (rank <= QUANTILE).astype(float)
        w_long = long.div(long.sum(axis=1), axis=0).fillna(0.0)
        w_short = short.div(short.sum(axis=1), axis=0).fillna(0.0)
        weights = 0.5 * w_long - 0.5 * w_short        # gross 1, dollar-neutral

        return (
            MarginPositions(
                weights=weights,
                margin_mode=MARGIN_MODE,
                max_leverage=MAX_LEVERAGE,
            ),
            CleanData(frames={"close": close}),
        )


# ─── Metadata — dash auto-registers via these ─────────────────────────────────
NAME        = "Universe momentum (30d, liquid)"
KIND        = "margin_weight"                           # "target_weight" also valid
PRESET      = "binance_um_perpetual"                    # contest rule — do not change
DESCRIPTION = "Cross-sectional 30d momentum over all USDT-perps with >$10M/day; long top quintile, short bottom; traded on the margin engine."


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

    # One run gives both the backtest *and* the executable order stream.
    res = run_backtest(bundle, start="2021-01-01", end=None, emit_orders=True)
    print(repr(res))
    print()
    print("Summary:")
    for k, v in res.summary().items():
        print(f"  {k:24s} {v}")

    # The live-trading bridge: the real BUY/SELL orders the engine placed —
    # exactly the shape you'd hand to an exchange.
    orders = getattr(res, "orders", [])
    print(f"\nOrder stream — {len(orders)} executable orders (first 8):")
    for o in orders[:8]:
        print(f"  {o.timestamp:%Y-%m-%d}  {o.symbol:14s} {o.side:4s} "
              f"qty={o.qty:<12.4f} @ {o.price:.6g}")

    nav_fig(res).show()


# ─── (Optional) Submit ────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     from framework import submit
#     submit(
#         Alpha(),
#         strategy_id="universe_momentum_v1",
#         name=NAME, preset=PRESET, description=DESCRIPTION,
#     )
