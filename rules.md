# Contest rules + gotchas

Expands on `README.md` §10. Run through this once before each submission.

---

## 1. Weekly deliverables (curriculum)

**The program plan (the PDF your admin shared) is the single source of truth for what each week's deliverable is.** This file does not redefine it — if the two ever disagree, follow the plan and tell your admin.

Two things to be clear about, because they trip people up:

- **Each week exercises *both* paradigms, not one.** W1's deliverable is **two alphas — one weight-based (`margin_weight`/`target_weight`) *and* one `order_book`** — not "weights only this week, orders next week." Later weeks add count and combine them into portfolios. See the plan for the exact per-week list.
- **Kind is never gated by code.** `submit()` accepts any kind any week; nothing is auto-rejected on kind, universe, or frequency. What actually governs a submission is (a) what you choose to submit and (b) your admin's review at the Thursday merge. The "themes" are a learning guide, not a filter.

**Weekly rankings are reported separately** — comparing scores across weeks isn't meaningful (different deliverables, and intraday frequency from W3 on).

**The three kinds** (set `KIND` in your file; the engine is chosen from it):

- **`margin_weight`** — *the default*. Return a weight matrix; it's traded **statefully** on real cash/positions with a leverage cap, liquidation, and funding. At 1× gross it reproduces `target_weight` exactly (no decomposition gap); above 1× you actually use leverage. Run with `emit_orders=True` to also get the executable BUY/SELL order stream (the live-trading bridge). Control leverage/mode by returning `MarginPositions(weights, max_leverage=…, margin_mode="cross"|"isolated")` instead of `Positions`.
- **`target_weight`** — the same weights on the lighter vectorized engine (no leverage/liquidation/funding state). Pick it if you don't want margin mechanics.
- **`order_book`** — emit an explicit BUY/SELL order list; single-asset, event-driven state machine.

---

## 2. Universe — any Binance USDT-perp

The universe is **every USDT-margined perpetual on Binance** (500+ symbols). The 1d klines for all of them ship in the **seed cache**, and any symbol is fetchable on demand — see [`README.md`](./README.md) §9 (seed + `update_cache()` / `fetch_all_1d()`).

The **9 majors** (`MAJORS_9`) are the liquid core and a sensible default:

```
btcusdt  ethusdt  solusdt  bnbusdt  xrpusdt
adausdt  dogeusdt  avaxusdt  linkusdt
```

Single-asset alphas (order_book) pick one symbol; multi-asset alphas (target_weight) use any set. You're free to go beyond the majors — but mind two things: **liquidity** (many alts are thinly traded; the cost model will punish high turnover there) and **history** (some coins listed only recently — e.g. XAUT since 2026 — so a long backtest comes out short or noisy). The built-in reference alphas all use `MAJORS_9`.

**Still not allowed:**
- Symbol-name typos (`btc-usdt`, `BTC/USDT`, uppercase `BTCUSDT`, etc.) — exact form is lowercase `<base>usdt`
- Things with no Binance USDT-perp (spot-only tokens, other quote currencies) — they won't fetch

### 2.1 Liquidity — gate, then trust the cost model

The 500+ universe includes a long tail of microcaps with erratic data. Three things keep that honest:

1. **Gate your universe** by dollar volume — the contest floor is **$10M average daily dollar volume** (~184 symbols clear it). One call:
   ```python
   from feeds import liquid_universe
   universe = liquid_universe(min_dollar_volume=10_000_000)   # or top_n=100 for a rank-based cut
   ```
   Build your alpha on `universe` rather than the raw 500+. Below this floor the data is mostly noise.
2. **Market impact** (margin engine) — if you do trade thin names, passing a `volume` frame with `impact_bp` charges extra cost ∝ (your trade / the day's dollar volume), so size in a thin coin is punished. *At a $10k account this is barely binding* — a $30k (3×) trade is ~0.3% of a $10M/day book — so the $10M gate is about data quality, not impact.
3. **Delisting / data gaps** — a symbol whose data ends is carried at its last price (not a phantom −100%); you can't size into a no-data bar.

### 2.2 History — short series come out noisy

Some coins listed only recently (e.g. XAUT since 2026), so a long backtest on them is short or noisy. Check `Dataset.load(...).index[0]` before leaning on a result.

---

## 3. Cost model — `binance_um_perpetual` preset everywhere

All alphas evaluated under the same cost preset:

| Item | Value |
|---|---|
| Exchange / market | Binance UM (USDⓈ-M perpetual) |
| Initial cash | 10000 USDT |
| Buy fee | 5 bp |
| Sell fee | 5 bp |
| Slippage | 5 bp |
| Annualization factor | 365 (crypto) |

**Do NOT use `Alpha.cost_overrides`.** Setting costs to zero inside your alpha to inflate Sharpe is a fairness violation. The admin will check.

During iteration, calling `run_backtest(bundle, buy_bp=0, sell_bp=0, slip_bp=0)` in your own notebook for a gross sanity-check is fine — that's just exploring your signal. But the submitted `meta.json` must declare `binance_um_perpetual` and have no overrides.

---

## 4. Data gotchas

### 4.1 `holdout_recent` default

`Dataset.load(identity, pandas=True)` defaults to `holdout_recent=True`, which trims the last 30 days. **Always specify `holdout_recent=False`** for backtest code:

```python
# ❌ Wrong
close = Dataset.load("binance.klines.um.btcusdt.1d", pandas=True)["Close"]
# In May you'd only see data through ~mid April

# ✅ Right
close = Dataset.load("binance.klines.um.btcusdt.1d",
                     pandas=True, holdout_recent=False)["Close"]
```

Built-in DataModules (`BinanceMajorsClose` etc.) pass `False` automatically. The single-file inline pattern is where this gets forgotten.

### 4.2 Lookahead — two places `.shift(1)` matters

**Weight-based alphas (`margin_weight` / `target_weight`):**
- If your signal uses today's close, you can't act on that signal at today's close (lookahead)
- **Both engines internally use `weights[t-1]`** → if you call `.shift(1)` yourself, you'll be **double-shifting** (= 2-day lag)
- So return `weights` as computed from today's close (decision-time); the engine handles the lag

**`order_book` alphas:**
- Apply `.shift(1)` explicitly when using rolling windows on the same bar's price
- E.g.: `upper = close.rolling(20).max().shift(1)` ← "max of the prior 20 days"
- Without it, today's price is included in its own rolling max → false-positive breakouts

### 4.3 NaN handling

- `dropna(how="any")` keeps only dates where all 9 symbols had data (e.g., from 2020-09-23 onwards)
- Or use `dropna(how="all")` and make your signal/position NaN-safe per-column

The built-in alphas use `dropna(how="any")`. Single-file templates do the same.

---

## 5. Signal / position gotchas

### 5.1 Cross-sectional z-score / rank doesn't work single-asset

Operations like `(x - x.mean(axis=1)) / x.std(axis=1)` need N≥2 symbols. With 1 symbol, the denominator is 0 → all NaN.

Fix:
- Use multi-asset (natural for target_weight)
- Or for single-asset, use time-series z-score: `(x - x.rolling(N).mean()) / x.rolling(N).std()`

### 5.2 NAV → 0 (ruin) in order_book

The order_book engine halts trading + marks `ruined=True` when NAV ≤ `run_threshold`. Once ruined, all subsequent trades are invalid.

Common causes:
- Heavy short + sharp upward move (price impact in the wrong direction)
- Notional too large (`NOTIONAL > starting_cash` = over-leveraged from day 1)

Recommended: `NOTIONAL == starting_cash` for ~1x leverage.

The **margin engine** has the same failure mode: cross-margin marks `ruined=True` if the whole account is liquidated, isolated forfeits the liquidated leg's margin. Keep `max_leverage` modest and the book diversified.

### 5.3 What `weights.sum(axis=1)` means

In a weight-based (`margin_weight` / `target_weight`) alpha, the row sum of weights indicates:
- `≈ 1.0` → 100% long-only
- `≈ 0.0` → dollar-neutral L/S
- `< 0` → short bias on that day

Pick the normalization that matches what you want:
- Long-only top-K → `weights[t].sum() = 1`, all positive
- Dollar-neutral L/S → `weights[t].sum() = 0`, signs cancel
- Unit gross → `|weights[t]|.sum() = 1`, signs free

---

## 6. Validation that happens on submission

`export_submission` auto-validates:
- `positions.parquet` has a `DatetimeIndex`
- Columns are valid symbols
- NaN ratio isn't excessive

The admin additionally checks before merging:
- `meta.json` schema (all required keys present)
- preset is `binance_um_perpetual`
- no `cost_overrides`
- no symbol typos

After merge, if your alpha isn't showing up in dash next to others, ping the admin.

---

## 7. Multiple versions of the same alpha

Use a fresh `strategy_id` for each iteration:
- `rsi_reversion_v1`
- `rsi_reversion_v2_winsorized`
- `rsi_reversion_v3_funding_adjusted`

Each lives in its own folder → dash shows them all → you can see your own progression visibly.

**Forbidden:**
- Deleting earlier-version folders (history is preserved)
- Overwriting a `positions.parquet` that's already merged

---

## 8. Pre-PR checklist — run through this every time

- [ ] `KIND` is set (`margin_weight` default; any kind is accepted — pick the one matching your idea)
- [ ] `PRESET = "binance_um_perpetual"`
- [ ] No `cost_overrides` class variable
- [ ] Symbol names are lowercase with `usdt` suffix
- [ ] `Dataset.load` called with `holdout_recent=False`
- [ ] You did NOT call `.shift(1)` on weights yourself (engine handles it)
- [ ] Running `python my_alpha.py` (or pasting it into a Jupyter cell) returns a valid `SimulationResult` — no `ruined=True`
- [ ] Even with all costs set to 0 (`buy_bp=0, sell_bp=0, slip_bp=0`), Sharpe is ≥ 0 (signal itself has meaning)
- [ ] `strategy_id` doesn't collide with one of your existing folders
