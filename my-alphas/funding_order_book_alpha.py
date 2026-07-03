"""
Funding-rate order_book alpha — a worked example.

Most funding strategies in this SDK are `target_weight` (cross-sectional: rank
the 9 majors by funding and long/short across them). This file shows the *other*
shape: a single-asset, event-driven `order_book` alpha whose trigger is the
perpetual **funding rate** rather than price.

Hypothesis — funding as a demand / sentiment filter (long / flat):
  - Funding is what longs pay shorts (or vice-versa) every 8h to keep the perp
    pinned to spot. In crypto it is structurally **positive** — the perp trades
    at a premium because leveraged demand skews long. Sustained positive funding
    therefore reads as genuine directional *demand*: be long.
  - When funding fades to ~zero or **negative**, leveraged demand has dried up:
    step aside to **flat** (rather than shorting a structurally-rising asset).
  So: average funding above +THRESHOLD → LONG, otherwise → FLAT. The regime only
  flips occasionally, which is exactly the discrete entry/exit logic the
  `order_book` paradigm is built for. The effect is a market-timing overlay —
  long through demand-driven rallies, side-lined through funding droughts.

  Two easy variants to try: (a) add a short leg by subtracting
  `(avg_funding < -THRESHOLD)` below — but note a 1x short on a structurally
  rising asset can ruin; (b) flip the sign for the contrarian "crowded longs ⇒
  fade" reading.

This is a price-PnL backtest (the engine prices fills off `close`); the funding
rate is used purely as the *timing signal*, not as a carry/income stream.

Edit the line marked "← write your signal here" to plug in your own funding
idea, then run the whole file (Shift+Enter in Jupyter, or
`python funding_order_book_alpha.py`).

Defaults shipped here:
  - asset:    BTC only (order_book is single-asset by contract)
  - signal:   sign of 7-day average daily funding, with a dead-band threshold
  - sizing:   $10,000 notional per entry on $10,000 starting cash → 1x

See ../rules.md for the per-week rules and ../alpha_anatomy.md for the contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from feeds import Dataset
from framework.types import CleanData, OrderList


# ─── Symbol + parameters (edit if needed) ─────────────────────────────────────
SYMBOL    = "btcusdt"      # ← pick one of the 9 majors
LOOKBACK  = 7              # days to average funding over
THRESHOLD = 0.0001         # dead-band on avg daily funding (~1bp/day) before acting
NOTIONAL  = 10000.0        # dollar size per entry
START     = 10000.0        # starting cash (NOTIONAL/START = 1.0 → 1x leverage)


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
        # 1. Price — single-asset daily close as a 1-column wide DataFrame.
        #    `holdout_recent=False` is required — the default True silently
        #    trims the last 30 days.
        close_df = Dataset.load(
            f"binance.klines.um.{SYMBOL}.1d",
            pandas=True, holdout_recent=False,
        )["Close"].to_frame(SYMBOL)
        px = close_df.iloc[:, 0]

        # 2. Funding — 8-hourly funding rate, collapsed to one number per day.
        #    `funding_datetime` is the tz-naive settlement time; summing the
        #    (3) daily settlements gives that day's total funding.
        fund = Dataset.load(
            f"binance.fundingrate.um.{SYMBOL}",
            pandas=True, holdout_recent=False,
        )
        fr = pd.Series(
            fund["funding_rate"].to_numpy(),
            index=pd.to_datetime(fund["funding_datetime"]),
        )
        daily_funding = fr.resample("1D").sum()

        # 3. Signal — your alpha logic goes here.   ←  write your signal here
        #    Default: long while LOOKBACK-day average daily funding confirms
        #    demand, otherwise flat. Output is a Series of integers in {0, +1}
        #    (NaN during warmup is fine). The state machine below also handles
        #    -1, so you can add a short leg by uncommenting the second term.
        avg_funding = daily_funding.rolling(LOOKBACK).mean().reindex(px.index).ffill()
        signal = (
            (avg_funding > THRESHOLD).astype(int)        # positive demand → long
            # - (avg_funding < -THRESHOLD).astype(int)   # uncomment to add a short leg
        )

        # 4. State machine — trade only on signal flips.
        orders: list[Order] = []
        position = 0.0
        prev_sig = 0
        for ts, price in px.items():
            sig_val = signal.loc[ts]
            if pd.isna(sig_val):
                continue
            cur = int(sig_val)
            if cur == prev_sig:
                continue                       # regime unchanged → hold

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
                    orders.append(Order(ts, "BUY", qty, price, "open long (funding > 0)"))
                    position = +qty
                else:
                    orders.append(Order(ts, "SELL", qty, price, "open short (funding < 0)"))
                    position = -qty
            prev_sig = cur

        return (
            OrderList(orders=orders, starting_cash=START),
            CleanData(frames={"close": close_df}),
        )


# ─── Metadata — dash auto-registers via these ─────────────────────────────────
NAME        = "BTC funding demand (7d, order_book)"
KIND        = "order_book"
PRESET      = "binance_um_perpetual"                    # contest rule — do not change
DESCRIPTION = "Single-asset state machine: long when 7d avg funding is positive (demand), short when negative."


# ─── Copy-paste runner ────────────────────────────────────────────────────────
# Running the file directly (`python funding_order_book_alpha.py`) or pasting the
# whole file into a Jupyter cell triggers a backtest + inline NAV chart.

if __name__ == "__main__":
    from framework import evaluate_alpha
    from backtest import run_backtest, nav_fig

    bundle = evaluate_alpha({
        "alpha_cls": Alpha,
        "kind":      KIND,
        "name":      NAME,
        "preset":    PRESET,
    })
    # start=None replays the full order history. An order_book backtest must not
    # be sliced mid-position: if `start` lands while a long is open, the engine
    # begins flat and the first in-window order is an orphan "close", leaving the
    # NAV stuck flat. Begin at the first order (or earlier) to stay consistent.
    res = run_backtest(bundle, start=None, end=None)
    print(repr(res))
    print()
    print("Summary:")
    for k, v in res.summary().items():
        print(f"  {k:24s} {v}")
    nav_fig(res).show()


# ─── (Optional) Submit ────────────────────────────────────────────────────────
# When you're happy with the alpha, uncomment the block below to push it to your
# branch of njt-submissions. `submit()` converts order_book → target_weight
# positions automatically (original KIND is preserved as `source_kind` in
# meta.json), then commits + pushes your whole workspace (code included)
# straight to the branch you're on — no PR, nothing to merge.
#
# if __name__ == "__main__":
#     from framework import submit
#     submit(
#         Alpha(),
#         strategy_id="funding_contrarian_v1",        # folder name (your choice)
#         name=NAME, preset=PRESET, description=DESCRIPTION,
#     )
