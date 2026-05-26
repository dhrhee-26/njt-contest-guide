"""
TEMPLATE — target_weight alpha (cross-sectional / portfolio pattern, single file).

Copy this file, then change only the line marked "← write your signal here"
to your own signal. Running the file as-is (`python my_alpha.py`) prints a
SimulationResult and opens an interactive NAV chart.

Default signal: 10-day cross-sectional momentum, long top half / short bottom
half (equal-weight). Default universe: BTC + ETH only — keeps the first data
fetch under a minute. Expand SYMBOLS to the full 9 majors (see rules.md) for
your real submission.

---

For contest W1 (target_weight, 1d). See ../rules.md for the full rules.
"""

from __future__ import annotations

import pandas as pd

from feeds import Dataset
from framework.types import CleanData, Positions


# ─── Universe + parameters (edit if needed) ───────────────────────────────────
# Starter universe: BTC + ETH only, for a fast first run. Add the other 7
# majors ("solusdt", "bnbusdt", "xrpusdt", "adausdt", "dogeusdt", "avaxusdt",
# "linkusdt") to broaden the cross-section for your real submission.
SYMBOLS = ["btcusdt", "ethusdt"]
LOOKBACK = 10


class Alpha:
    def get(self) -> tuple[Positions, CleanData]:
        # 1. Data — daily close per symbol as a wide DataFrame (date × symbol).
        #    `holdout_recent=False` is required — the default True silently
        #    trims the last 30 days.
        close = pd.concat(
            {
                sym: Dataset.load(
                    f"binance.klines.um.{sym}.1d",
                    pandas=True, holdout_recent=False,
                )["Close"]
                for sym in SYMBOLS
            },
            axis=1,
        ).dropna(how="any")

        # 2. Signal — your alpha logic goes here.   ←  write your signal here
        #    Below is the default: 10-day cross-sectional momentum.
        signal = close.pct_change(LOOKBACK)

        # 3. Position — cross-sectional rank → long top half, short bottom half,
        #    equal weights. Change this block if you want a different
        #    normalization (long-only top-K, dollar-neutral, etc.).
        rank = signal.rank(axis=1, pct=True)
        n = close.shape[1]
        half = n / 2
        weights = pd.DataFrame(0.0, index=close.index, columns=close.columns)
        weights[rank > 0.5]  = +1.0 / half     # top half long
        weights[rank <= 0.5] = -1.0 / half     # bottom half short

        return Positions(weights=weights), CleanData(frames={"close": close})


# ─── Metadata — dash auto-registers via these ─────────────────────────────────
NAME        = "My target-weight alpha"                  # ← your alpha name
KIND        = "target_weight"
PRESET      = "binance_um_perpetual"                    # contest rule — do not change
DESCRIPTION = "One-line description — what signal is this?"


# ─── Copy-paste runner ────────────────────────────────────────────────────────
# Running the file directly (`python my_alpha.py`) or pasting the whole file
# into a Jupyter cell triggers a backtest + inline NAV chart. dash's registry
# imports the file with __name__ != "__main__", so this block stays silent
# when the alpha is being auto-discovered.

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
# your branch of njt-submissions. `submit()` writes positions.parquet +
# meta.json under /submissions/interns/<your-handle>/<strategy_id>/, then
# git add / commit / push, then prints a clickable PR-creation URL. Your
# handle is auto-detected from the current branch name.
#
# if __name__ == "__main__":
#     from framework import submit
#     submit(
#         Alpha(),
#         strategy_id="my_alpha_v1",                  # folder name (your choice)
#         name=NAME, preset=PRESET, description=DESCRIPTION,
#     )
