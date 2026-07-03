"""
Donchian breakout on a liquid coin — order_book.

order_book is single-asset, so it doesn't use the cross-sectional panel — but it
*does* benefit from the expanded universe: you can now trade any USDT-perp, and
`liquid_universe()` picks a tradeable one for you. This file shows how to choose
a liquid symbol and run a classic trend state machine on it.

The alpha: a Donchian channel breakout. Go long when the close makes a new
ENTRY-day high; exit to flat when it makes a new EXIT-day low. Trades only on
those flips — exactly the discrete entry/exit logic order_book is built for.

Edit the line marked "← write your signal here". Run the whole file
(`python3 breakout_order_book_alpha.py`). For contest W2 (order_book,
1d). Needs the seed cache extracted (README §9).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

from feeds import Dataset, liquid_universe
from framework.types import CleanData, OrderList


# ─── Symbol + parameters (edit if needed) ─────────────────────────────────────
# Pick a liquid symbol. The default is the most-liquid alt after the top few —
# swap in any name from `liquid_universe()`:
#     from feeds import liquid_universe
#     liquid_universe(top_n=20)   # -> ['btcusdt', 'ethusdt', 'solusdt', ...]
SYMBOL    = "solusdt"
ENTRY     = 20            # breakout lookback (new N-day high → enter long)
EXIT      = 10            # exit lookback (new M-day low → go flat)
NOTIONAL  = 10000.0       # dollar size per entry
START     = 10000.0       # starting cash


@dataclass(frozen=True)
class Order:
    timestamp: pd.Timestamp
    side: Literal["BUY", "SELL"]
    qty: float
    price: float
    reason: str


class Alpha:
    def get(self) -> tuple[OrderList, CleanData]:
        # (optional) sanity-check the symbol is liquid; warn if it isn't.
        if SYMBOL not in liquid_universe(min_dollar_volume=10_000_000):
            print(f"[warn] {SYMBOL} is below the $10M/day liquidity floor (rules §2.1)")

        # 1. Price — single-asset daily close.
        close_df = Dataset.load(
            f"binance.klines.um.{SYMBOL}.1d", pandas=True, holdout_recent=False,
        )["Close"].to_frame(SYMBOL)
        px = close_df.iloc[:, 0]

        # 2. Signal — your alpha logic goes here.   ←  write your signal here
        #    Default: Donchian breakout. +1 on a new ENTRY-day high, 0 on a new
        #    EXIT-day low; carry the state in between.
        upper = px.rolling(ENTRY).max()
        lower = px.rolling(EXIT).min()
        signal = pd.Series(0, index=px.index)
        state = 0
        for ts in px.index:
            if pd.notna(upper[ts]) and px[ts] >= upper[ts]:
                state = 1
            elif pd.notna(lower[ts]) and px[ts] <= lower[ts]:
                state = 0
            signal[ts] = state

        # 3. State machine — trade only on signal flips (long / flat).
        orders: list[Order] = []
        position = 0.0
        prev = 0
        for ts, price in px.items():
            cur = int(signal.loc[ts])
            if cur == prev:
                continue
            if cur == 1:                                   # breakout → open long
                qty = NOTIONAL / price
                orders.append(Order(ts, "BUY", qty, price, "breakout long"))
                position = qty
            elif position > 0:                             # breakdown → exit
                orders.append(Order(ts, "SELL", position, price, "exit to flat"))
                position = 0.0
            prev = cur

        return OrderList(orders=orders, starting_cash=START), CleanData(frames={"close": close_df})


# ─── Metadata — dash auto-registers via these ─────────────────────────────────
NAME        = "SOL Donchian breakout (20/10, order_book)"
KIND        = "order_book"
PRESET      = "binance_um_perpetual"                    # contest rule — do not change
DESCRIPTION = "Single-asset Donchian breakout: long on a 20d high, flat on a 10d low."


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
    res = run_backtest(bundle, start=None, end=None)   # order_book replays the full order list
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
#         strategy_id="breakout_v1",
#         name=NAME, preset=PRESET, description=DESCRIPTION,
#     )
