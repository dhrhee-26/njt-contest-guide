"""
TEMPLATE — portfolio (combine several alphas into one strategy, single file).

A portfolio blends alphas you have ALREADY SUBMITTED. It sums their target-weight
matrices in position space — so a long BTC in one alpha and a short BTC in another
actually net out, and the combined book is backtested ONCE with real turnover,
cost, leverage and (for margin) liquidation.

How it works:
  - List your submitted alphas by their strategy_id in `alpha_list` (the folder
    name you used in submit(...) — see your branch of njt-submissions).
  - The combined weights = Σ  allocation(alpha) · that alpha's weights.
  - `weight()` decides the allocation across alphas. Default is equal weight;
    override it for a dynamic scheme (inverse-vol, mean-variance, …).
  - Sub-alphas of ANY kind mix freely (target_weight / order_book / margin_weight)
    — they all reduce to a weight matrix. The COMBINED book is replayed with the
    one `KIND` you pick below (margin_weight by default, like a single alpha).

Copy this file, set `alpha_list` to your strategy_ids, and (optionally) write a
`weight()`. Running the file as-is (`python my_portfolio.py`) prints a
SimulationResult and opens an interactive NAV chart. See ../rules.md §1.1.
"""

from __future__ import annotations

from framework import BasePortfolio


class Portfolio(BasePortfolio):
    # ── Your submitted alphas, by strategy_id (the folder name from submit()) ──
    #    Replace these with YOUR strategy_ids. You can also pass an Alpha
    #    instance directly for an alpha you have not submitted yet.
    alpha_list = [
        "my_alpha_v1",          # ← your first submitted alpha
        "my_alpha_v2",          # ← your second
    ]

    # ── How the COMBINED book is traded (same choice as a single alpha) ───────
    KIND = "margin_weight"      # "target_weight" also valid
    max_leverage = 3.0          # used only when KIND == "margin_weight"
    margin_mode  = "cross"      # "cross" | "isolated"

    # ── Allocation across the alphas — DataFrame[date × alpha label] ──────────
    #    Default (inherited) is EQUAL WEIGHT. Uncomment to use a dynamic scheme:
    #
    # def weight(self):
    #     rets = self.alpha_returns()                    # each alpha's daily returns
    #     inv_vol = 1 / rets.rolling(30).std()           # inverse-volatility weight
    #     return inv_vol.div(inv_vol.sum(axis=1), axis=0)


# ─── Metadata — dash auto-registers via these ─────────────────────────────────
NAME        = "My Portfolio"                            # ← your portfolio name
KIND        = "margin_weight"                           # keep in sync with the class
PRESET      = "binance_um_perpetual"                    # contest rule — do not change
DESCRIPTION = "One-line description — how are the alphas combined?"


# ─── Copy-paste runner ────────────────────────────────────────────────────────
# Running the file directly (`python my_portfolio.py`) or pasting it into a
# Jupyter cell triggers a backtest + inline NAV chart. It also prints the
# correlation between your alphas (orthogonality) and a side-by-side comparison
# of the portfolio vs each individual alpha — useful for your report.

if __name__ == "__main__":
    from framework import evaluate_alpha
    from backtest import run_backtest, nav_fig

    pf = Portfolio()

    print("Alpha correlation (orthogonality):")
    print(pf.alpha_corr().round(2))
    print()

    bundle = evaluate_alpha({
        "alpha_cls": Portfolio,
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

    # Portfolio vs each individual alpha (NAV overlay + stats table).
    pf.compare().show()
    nav_fig(res).show()


# ─── (Optional) Submit ────────────────────────────────────────────────────────
# When you're happy with the portfolio, uncomment to push it to your branch.
# It submits exactly like an alpha — one folder, one commit, straight to your
# branch. No PR, nothing to merge.
#
# if __name__ == "__main__":
#     from framework import submit
#     submit(
#         Portfolio(),
#         strategy_id="my_portfolio_v1",              # folder name (your choice)
#         name=NAME, preset=PRESET, description=DESCRIPTION,
#     )
