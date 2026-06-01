# Contest rules + gotchas

Expands on `README.md` §10. Run through this once before each submission.

---

## 1. Per-week constraints (curriculum)

Each week of the contest exercises a different mental model:

| Week | Allowed KIND | Frequency | Learning focus |
|---|---|---|---|
| **W1** | `target_weight` only | daily (1d) | Cross-sectional thinking — rank, weight, dollar-neutral L/S |
| **W2** | `order_book` only | daily (1d) | Event / state-machine thinking, trend-following, regime detection |
| **W3+** | both | hourly (`.1h`) | Intraday reversal, microstructure |

Each week's alphas use only that week's KIND/frequency. A W1 alpha submitted as `order_book` will be auto-rejected.

**Weekly rankings are reported separately** — comparing a W1 score to a W2 score isn't meaningful (different constraints).

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

**`target_weight` alphas:**
- If your signal uses today's close, you can't act on that signal at today's close (lookahead)
- **The engine internally uses `weights[t-1]`** → if you call `.shift(1)` yourself, you'll be **double-shifting** (= 2-day lag)
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

### 5.3 What `weights.sum(axis=1)` means

In a `target_weight` alpha, the row sum of weights indicates:
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

- [ ] `KIND` matches what the current week allows (W1: target_weight / W2: order_book)
- [ ] `PRESET = "binance_um_perpetual"`
- [ ] No `cost_overrides` class variable
- [ ] Symbol names are lowercase with `usdt` suffix
- [ ] `Dataset.load` called with `holdout_recent=False`
- [ ] You did NOT call `.shift(1)` on weights yourself (engine handles it)
- [ ] Running `python my_alpha.py` (or pasting it into a Jupyter cell) returns a valid `SimulationResult` — no `ruined=True`
- [ ] Even with all costs set to 0 (`buy_bp=0, sell_bp=0, slip_bp=0`), Sharpe is ≥ 0 (signal itself has meaning)
- [ ] `strategy_id` doesn't collide with one of your existing folders
