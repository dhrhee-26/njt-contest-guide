"""
TEMPLATE — order_book alpha (event / state-machine pattern, single file).

Copy this file, then change only the line marked "← write your signal here"
to your own signal. Running the file as-is (`python my_alpha.py`) prints a
SimulationResult and opens an interactive NAV chart.

Default signal: SMA(5) > SMA(20) → long; SMA(5) < SMA(20) → short. Single
asset (BTC).

---

For contest W2 (order_book, 1d, single asset). See ../rules.md for the full rules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from feeds import Dataset
from framework.types import CleanData, OrderList


# ─── Symbol + parameters (edit if needed) ─────────────────────────────────────
SYMBOL   = "btcusdt"       # ← pick one of the 9 majors
FAST     = 5
SLOW     = 20
NOTIONAL = 10000.0         # dollar size per entry
START    = 10000.0         # starting cash (NOTIONAL/START = 1.0 → 1x leverage)


@dataclass(frozen=True)
class Order:
    """Engine only reads timestamp/side/qty/price (duck-typed)."""
    timestamp: pd.Timestamp
    side: Literal["BUY", "SELL"]
    qty: float
    price: float
    reason: str


class Alpha:
    def get(self) -> tuple[OrderList, CleanData]:
        # 1. Data — single-asset close as a 1-column wide DataFrame.
        #    `holdout_recent=False` is required — the default True silently
        #    trims the last 30 days.
        close_df = Dataset.load(
            f"binance.klines.um.{SYMBOL}.1d",
            pandas=True, holdout_recent=False,
        )["Close"].to_frame(SYMBOL)
        px = close_df.iloc[:, 0]

        # 2. Signal — your alpha logic goes here.   ←  write your signal here
        #    Below is the default: SMA crossover.
        #    Output should be a Series of integers in {-1, 0, +1}. NaN is OK
        #    during warmup.
        sma_fast = px.rolling(FAST).mean()
        sma_slow = px.rolling(SLOW).mean()
        signal = (sma_fast > sma_slow).astype(int) - (sma_fast < sma_slow).astype(int)

        # 3. State machine — trade only on signal flips.
        orders: list[Order] = []
        position = 0.0
        prev_sig = 0
        for ts, price in px.items():
            sig_val = signal.loc[ts]
            if pd.isna(sig_val):
                continue
            cur = int(sig_val)
            if cur == prev_sig:
                continue                       # signal unchanged → hold

            # Close existing position
            if position > 0:
                orders.append(Order(ts, "SELL", position, price,
                                    f"close long ({prev_sig}->{cur})"))
            elif position < 0:
                orders.append(Order(ts, "BUY", -position, price,
                                    f"close short ({prev_sig}->{cur})"))
            position = 0.0

            # Open new position
            if cur != 0:
                qty = NOTIONAL / price
                if cur == +1:
                    orders.append(Order(ts, "BUY", qty, price, "open long"))
                    position = +qty
                else:
                    orders.append(Order(ts, "SELL", qty, price, "open short"))
                    position = -qty
            prev_sig = cur

        return (
            OrderList(orders=orders, starting_cash=START),
            CleanData(frames={"close": close_df}),
        )


# ─── Metadata — dash auto-registers via these ─────────────────────────────────
NAME        = "My order-book alpha"                     # ← your alpha name
KIND        = "order_book"
PRESET      = "binance_um_perpetual"                    # contest rule — do not change
DESCRIPTION = "One-line description — what signal is this?"


# ─── Copy-paste runner ────────────────────────────────────────────────────────
# Running the file directly (`python my_alpha.py`) or pasting the whole file
# into a Jupyter cell triggers a backtest + inline NAV chart.

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
# When you're happy with the alpha, uncomment the block below to push it to
# your branch of njt-submissions. `submit()` converts order_book → target_weight
# positions automatically (the on-disk format is unified; original KIND is
# preserved as `source_kind` in meta.json), then git add / commit / push, then
# prints a clickable PR-creation URL. Your handle is auto-detected from the
# current branch name.
#
# if __name__ == "__main__":
#     from framework import submit
#     submit(
#         Alpha(),
#         strategy_id="my_alpha_v1",                  # folder name (your choice)
#         name=NAME, preset=PRESET, description=DESCRIPTION,
#     )
