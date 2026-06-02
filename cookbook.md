# NJT Contest — Data & Strategy Cookbook

*Last updated: 2026-06-02*

A practical, example-driven companion to `README.md`, `rules.md`, and
`alpha_anatomy.md`. Everything here is copy-paste runnable from a Jupyter cell
(http://localhost:8888). It answers the questions that come up most:

0. [One-time setup — tell `submit()` your handle (`.env`)](#0-one-time-setup)
1. [Loading & updating data — every `Dataset.load` parameter](#1-loading--updating-data)
2. [Loading every symbol at once (whole-universe panel)](#2-whole-universe-panel-load)
3. [Liquidity — why thin coins are filtered, and how the backtest models them](#3-liquidity)
4. [The three kinds — `target_weight` / `order_book` / `margin_weight`](#4-the-three-kinds), and [running a backtest](#44-running-a-backtest--parameters)
5. [Seeing your cached data in the dash Data Monitor](#5-viewing-data-in-the-dash)
6. [Searching the Data Monitor by Name](#6-searching-by-name)
7. [Seeing other interns' submissions in the dash](#7-seeing-others-submissions)

---

## 0. One-time setup

Two clones + one tiny file, then you're done — **you never check out a branch.**

```bash
git clone https://github.com/dhrhee-26/njt-contest-guide.git ~/njt-contest
cd ~/njt-contest
git clone git@github.com:dhrhee-26/njt-submissions.git     # leave it on main
echo "NJT_HANDLE=<your-handle>" > .env                     # ← this is the whole "setup"
docker compose up -d                                       # http://localhost:8888 + :8050
```

**What `.env` is:** a one-line file in `~/njt-contest/` (next to `docker-compose.yml`)
holding your contest handle, e.g.:

```
NJT_HANDLE=alice
```

`docker compose` reads `.env` automatically and passes `NJT_HANDLE` into the
container, where `submit()` uses it to push your work to `interns/<your-handle>`
— without you ever switching branches. Keep `njt-submissions` on `main` and just
`git pull` to see merged + peer alphas (see §7).

- Change/fix it later: edit `~/njt-contest/.env`, then `docker compose up -d --force-recreate` so the container picks up the new value.
- Already cloned and on a branch from the old flow? Just add the `.env`, then `cd njt-submissions && git checkout main && cd ..` once. (Without `.env`, `submit()` still falls back to whatever `interns/<handle>` branch is checked out — nothing breaks.)
- **Never** put a password, GitHub token, or your private SSH key in `.env` — only the handle.

---

## 1. Loading & updating data

### 1.1 What data is available — the feeds

Everything is a **Binance** dataset, addressed by a dotted **identity string**:

```
binance.{category}.{market}.{symbol}.{interval}     # klines (has an interval)
binance.{category}.{market}.{symbol}                # funding / metrics (no interval)
binance.klines.{market}.{Field}.{interval}          # whole-universe panel (§2)
```

| Identity prefix | What it is |
|---|---|
| `binance.klines.um` | **USDⓈ-M perpetual futures OHLCV** (USDT/USDC-margined, e.g. `btcusdt`). Deepest derivatives liquidity — **the contest default.** |
| `binance.klines.cm` | COIN-M perpetual & delivery futures OHLCV (margined/settled in the coin, e.g. `btcusd_perp`). |
| `binance.klines.spot` | Spot-market OHLCV (physical asset vs USDT/BTC/FDUSD…). |
| `binance.fundingrate.um` | UM perpetual **funding rate** (exchanged every 8h; `+` = longs pay shorts = bullishly crowded). Crypto-native carry / sentiment signal. |
| `binance.metrics.um` | UM daily **positioning metrics**: open interest, top-trader / global long-short ratios, taker buy-vs-sell volume. |
| `binance.option.eoh` | Options end-of-hour summary — strike-level OI, volume, implied vol, greeks. |
| `binance.option.bvol` | Binance Volatility Index (BVOL, a "crypto VIX") for BTC/ETH. Large on disk. |

**OHLCV** = Open, High, Low, Close, Volume per candle. `um` (USDⓈ-M perps) is
what almost every contest alpha uses. **For W1/W2, stick to
`binance.klines.um.{symbol}.1d`** (daily UM klines); funding/metrics/options are
crypto-native extras you can bring in later (`rules.md`).

### 1.2 `Dataset.load`

Everything goes through `feeds.Dataset.load`. Full signature:

```python
Dataset.load(
    identity_name,                 # "binance.klines.um.btcusdt.1d", etc.
    update=False,                  # False | True | "append"
    pandas=False,                  # False → polars, True → pandas
    holdout_recent=True,           # True trims the LAST 30 DAYS — pass False for backtests
    min_dollar_volume=None,        # panel-only liquidity gate (see §3)
    liquidity_lookback=30,         # days averaged for that gate
)
```

| Parameter | Values / default | What it does |
|---|---|---|
| `identity_name` | required string | What to load. Single symbol `binance.klines.um.btcusdt.1d`, or a whole-universe panel `binance.klines.um.Close.1d` (see §2). Other feeds: `binance.fundingrate.um.btcusdt`, `binance.metrics.um.btcusdt`. |
| `update` | `False` *(default)* / `True` / `"append"` | `False` = use the cache if present, else fetch once. `True` = force a **full** re-fetch. `"append"` = fetch **only days newer** than your cache (fast incremental refresh). |
| `pandas` | `False` *(default)* / `True` | `False` returns a **polars** frame; `True` returns a **pandas** frame with OHLCV title-cased (`Open/High/Low/Close/Volume`) and a `DatetimeIndex`. Most alphas use `pandas=True`. |
| `holdout_recent` | `True` *(default)* / `False` | `True` silently **drops the most recent 30 days** (an out-of-sample buffer). **In backtest code always pass `False`** or your results are quietly short. |
| `min_dollar_volume` | `None` *(default)* / e.g. `10_000_000` | **Panel mode only.** Drops symbols whose average daily dollar volume is below the threshold. See §3. |
| `liquidity_lookback` | `30` *(default)* | Days averaged when applying `min_dollar_volume`. |

**One symbol:**
```python
from feeds import Dataset
btc = Dataset.load("binance.klines.um.btcusdt.1d", pandas=True, holdout_recent=False)
btc[["Open", "High", "Low", "Close", "Volume"]].tail()
```

**Bring your cache up to date** (from a Jupyter cell — the Data Monitor tab is view-only):
```python
from feeds import update_cache, fetch_all_1d
update_cache()      # incrementally append new days to EVERY cached symbol (parallel). Returns (ok, failed).
fetch_all_1d()      # pull 1d for any newly-listed USDT-perp you don't have yet. Returns (ok, failed).
```
- `update_cache(workers=8)` — walks your cache and does `update="append"` on each file. Only new data is downloaded; safe to re-run.
- `fetch_all_1d(workers=12, missing_only=True)` — discovers every UM USDT-perp from the Binance Vision archive (works from the US) and fetches the ones you're missing. `missing_only=False` re-fetches all.

**Force-refresh or extend one symbol:**
```python
Dataset.load("binance.klines.um.solusdt.1h", update=True,  holdout_recent=False)  # full re-fetch (intraday, W3+)
Dataset.load("binance.klines.um.btcusdt.1d", update="append", holdout_recent=False)  # just the new tail
```
> Intraday (`1h`, `5m`, …) is **opt-in per symbol** — fetch only what you need. A 1-minute panel for the whole universe is multiple GB and is blocked (see §2).

---

## 2. Whole-universe panel load

To get **one OHLCV field across every cached symbol** in a single wide DataFrame
(date × symbol) — ideal for cross-sectional alphas — use a **capitalized field
name** in place of the symbol:

```python
from feeds import Dataset

close = Dataset.load("binance.klines.um.Close.1d", pandas=True, holdout_recent=False)
close.shape        # (T, ~500+)  — every USDT-perp's daily close at once
```

Valid panel fields: **`Open`, `High`, `Low`, `Close`, `Volume`**. So
`binance.klines.um.Open.1d`, `…High.1d`, `…Volume.1d`, etc.

```python
open_  = Dataset.load("binance.klines.um.Open.1d",  pandas=True, holdout_recent=False)
high   = Dataset.load("binance.klines.um.High.1d",  pandas=True, holdout_recent=False)
volume = Dataset.load("binance.klines.um.Volume.1d", pandas=True, holdout_recent=False)
```

Notes:
- The panel is **assembled from your cache** — it never triggers a download. Extract the seed cache (README §9) and/or run `fetch_all_1d()` first, or you'll only see the handful of symbols you have.
- A symbol not yet listed on a given date is `NaN` there — `.dropna(how="any")` to inner-join, or let `rank()`/`mean()` skip NaNs.
- Coarser intervals work (`Close.1h`, `Close.4h`, `Close.1d`, …). **Sub-hourly panels (`Close.5m`) are blocked** — a 500-symbol minute matrix is multiple GB. Single-symbol sub-hourly is fine.

---

## 3. Liquidity

Crypto has a long tail of coins that barely trade. On a thin coin you can't
actually fill size — the spread is wide, the book is shallow, and a backtest
that assumes you bought $1M of it at the close is fiction. Two tools keep your
alphas honest.

**(a) Filter the universe to liquid names.** Either inline on the panel, or as a symbol list:
```python
from feeds import Dataset, liquid_universe

# inline: drop anything under $10M/day average over the last 30 days (~184 symbols clear)
close = Dataset.load("binance.klines.um.Close.1d", pandas=True, holdout_recent=False,
                     min_dollar_volume=10_000_000)

# or get the list of liquid symbols, ranked most-liquid first:
liquid_universe(top_n=50)                       # 50 most-liquid USDT-perps
liquid_universe(min_dollar_volume=10_000_000)   # everything above $10M/day
```
Dollar volume = `close × volume` averaged over `lookback_days` (default 30). The
`MAJORS_9` set (`btcusdt ethusdt solusdt bnbusdt xrpusdt adausdt dogeusdt avaxusdt linkusdt`)
is the liquid core and a safe default.

**(b) The backtest itself penalizes illiquidity** so you can't game thin names:
- **Cost model** — every fill pays `5 bp fee + 5 bp slippage` (the `binance_um_perpetual` preset). High turnover in thin names bleeds.
- **Market impact** (margin engine) — optional extra slippage proportional to your trade size vs. the coin's daily dollar volume: a big order in a thin book costs more. Moving size where there's no volume is punished.
- **Delisting / data gaps** — a coin whose data ends (e.g. MATIC's perp was delisted 2024-08-12) is **carried at its last price, not zeroed** — no phantom total loss — and the engine **won't let you trade a symbol on a bar where it has no real data** (the weight is forced flat there).

See `rules.md` §2.1 for the official liquidity handling.

---

## 4. The three kinds

Your alpha is a single class `Alpha` with a `get()` method and four module-level
constants (`NAME`, `KIND`, `PRESET`, `DESCRIPTION`). The **`KIND`** decides which
engine runs and what `get()` returns. **No kind is gated by week — submit
whatever fits your idea** (`rules.md` §1).

| Kind | Returns | Engine | Use it for |
|---|---|---|---|
| `margin_weight` *(default)* | `MarginPositions(weights=…)` | Stateful multi-asset: real cash/positions, leverage cap, liquidation, funding | Cross-sectional weight alphas, **with** leverage/liquidation modeled. Also emits the executable BUY/SELL order stream. |
| `target_weight` | `Positions(weights=…)` | Vectorized weights, no margin mechanics | The same weight idea, lighter, when you don't want leverage/liquidation/funding state. |
| `order_book` | `OrderList(orders=[…])` | Single-asset event/state machine | Trend / breakout / regime alphas that act on **signal flips**, one symbol. |

### 4.0 What you import & return — `framework.types`

`get()` always returns a **2-tuple**: `(your_position_object, CleanData)`. The
import line tells the SDK which kind you're building, because the **type of the
position object decides the kind** (not a string you set):

```python
from framework.types import CleanData, Positions          # target_weight
from framework.types import CleanData, MarginPositions     # margin_weight
from framework.types import CleanData, OrderList           # order_book
```

| Type | Fields | Meaning |
|---|---|---|
| `CleanData` | `frames: dict[str, DataFrame]` | Your data, keyed by name — **must contain `"close"`**. The engine reads `frames["close"]` (and `high`/`low` for margin liquidation if you provide them). |
| `Positions` | `weights: DataFrame` | A `target_weight` position. |
| `MarginPositions` | `weights: DataFrame`, `margin_mode="cross"`, `max_leverage=3.0`, `maintenance_margin=0.05`, `starting_cash=10_000.0` | A `margin_weight` position — same `weights`, plus how it's traded with leverage. |
| `OrderList` | `orders: list`, `starting_cash=10_000.0` | An `order_book` position — an explicit list of order objects. |

**What each position looks like:**

`Positions` / `MarginPositions` — a **wide weight matrix** (date × symbol). Each
row is decision-time target weights (the engine lags it 1 day for you):

```
weights:                btcusdt   ethusdt   solusdt   ...
            2021-01-01     0.20     -0.10      0.00
            2021-01-02     0.15      0.00     -0.05    →  Positions(weights=…)
            ...                                            MarginPositions(weights=…, max_leverage=2.0)
```
`+0.2` = 20% of NAV long that symbol that day; `-0.1` = 10% short; row sum 0 =
dollar-neutral, row sum 1 = 100% long-only. Same shape for both — `MarginPositions`
just adds the margin knobs (leverage cap, cross/isolated, maintenance, cash).

`OrderList` — a **chronological list of order objects**, one symbol, emitted only
on signal flips:

```
orders = [
    Order(2021-03-04, "BUY",  0.27, 38500.0, "open"),    →  OrderList(orders=[…], starting_cash=10000.0)
    Order(2021-05-12, "SELL", 0.27, 57200.0, "close"),
    ...
]
```
Each `Order` is a small `@dataclass` you define with `timestamp / side / qty / price`
(+ optional `reason`) — see §4.3.

---

### 4.1 `target_weight` — cross-sectional / portfolio
You output, for each day, a **weight per symbol** (a row of a date × symbol
matrix). `+0.2` = 20% of NAV long that symbol that day; `-0.1` = 10% short;
row sum 0 = dollar-neutral long/short, row sum 1 = 100% long-only. The engine
lags weights by one day for you (**do not `.shift(1)` yourself**) and applies
costs.

```python
import pandas as pd
from feeds import Dataset
from framework.types import CleanData, Positions

SYMBOLS, LOOKBACK = ["btcusdt","ethusdt","solusdt","bnbusdt","xrpusdt",
                     "adausdt","dogeusdt","avaxusdt","linkusdt"], 60

class Alpha:
    def get(self):
        close = pd.concat({s: Dataset.load(f"binance.klines.um.{s}.1d",
                          pandas=True, holdout_recent=False)["Close"] for s in SYMBOLS},
                          axis=1).dropna(how="any")
        signal = close.pct_change(LOOKBACK)                 # 60-day momentum
        rank   = signal.rank(axis=1, pct=True)              # cross-sectional rank
        half   = close.shape[1] / 2
        w = pd.DataFrame(0.0, index=close.index, columns=close.columns)
        w[rank > 0.5], w[rank <= 0.5] = +1.0/half, -1.0/half   # long top half / short bottom
        return Positions(weights=w), CleanData(frames={"close": close})

NAME, KIND, PRESET = "60d Mom L/S (9 majors)", "target_weight", "binance_um_perpetual"
DESCRIPTION = "Cross-sectional 60d momentum, equal-weight long/short."
```

### 4.2 `margin_weight` — weights, traded for real (the default)
Identical idea to `target_weight` — you still output a weight matrix — but the
engine trades it **statefully**: it holds cash and positions, caps gross
leverage, can **liquidate** you if a leveraged book blows through maintenance
margin, and charges **funding**. At 1× gross with no liquidation it reproduces
`target_weight` exactly (to machine precision); above 1× you actually use
leverage. Return `MarginPositions` and (optionally) set leverage/mode:

```python
from framework.types import CleanData, MarginPositions

class Alpha:
    def get(self):
        close = Dataset.load("binance.klines.um.Close.1d", pandas=True,
                             holdout_recent=False, min_dollar_volume=10_000_000)
        rank  = close.pct_change(30).rank(axis=1, pct=True)
        long  = (rank >= 0.8).astype(float); short = (rank <= 0.2).astype(float)
        w = 0.5*long.div(long.sum(1),axis=0).fillna(0) - 0.5*short.div(short.sum(1),axis=0).fillna(0)
        return MarginPositions(weights=w, margin_mode="cross", max_leverage=3.0), \
               CleanData(frames={"close": close})

NAME, KIND, PRESET = "Universe momentum (30d, liquid)", "margin_weight", "binance_um_perpetual"
DESCRIPTION = "30d momentum over all USDT-perps >$10M/day; long top quintile / short bottom."
```
- `margin_mode="cross"` — one shared margin pool; a loss anywhere can liquidate the whole book. `"isolated"` — per-leg margin; one leg can blow up without taking the rest.
- `max_leverage` — gross-notional / equity cap. Exceed it and the engine scales you down.
- `emit_orders=True` on `run_backtest` returns the **executable BUY/SELL order stream** (timestamp/symbol/side/qty/price) — the same orders you'd send to an exchange. The backtest and the live order list come out of one run.

### 4.3 `order_book` — event / state machine (single asset)
You emit an explicit, time-ordered list of `BUY`/`SELL` orders for **one**
symbol — natural for trend-following, breakouts, regime switches. Trade only
when the signal flips; close the old position before opening the new one.

```python
from dataclasses import dataclass
from typing import Literal
import pandas as pd
from feeds import Dataset
from framework.types import CleanData, OrderList

SYMBOL, FAST, SLOW, NOTIONAL = "btcusdt", 5, 20, 10_000.0

@dataclass(frozen=True)
class Order:
    timestamp: pd.Timestamp; side: Literal["BUY","SELL"]; qty: float; price: float; reason: str

class Alpha:
    def get(self):
        cdf = Dataset.load(f"binance.klines.um.{SYMBOL}.1d", pandas=True,
                           holdout_recent=False)["Close"].to_frame(SYMBOL)
        px  = cdf.iloc[:, 0]
        sig = (px.rolling(FAST).mean() > px.rolling(SLOW).mean()).astype(int) \
            - (px.rolling(FAST).mean() < px.rolling(SLOW).mean()).astype(int)
        orders, pos, prev = [], 0.0, 0
        for ts, price in px.items():
            cur = int(sig.loc[ts]) if not pd.isna(sig.loc[ts]) else prev
            if cur == prev: continue
            if pos != 0:                                      # close existing
                orders.append(Order(ts, "SELL" if pos>0 else "BUY", abs(pos), price, "close")); pos = 0.0
            if cur != 0:                                      # open new
                qty = NOTIONAL/price
                orders.append(Order(ts, "BUY" if cur>0 else "SELL", qty, price, "open"))
                pos = qty if cur>0 else -qty
            prev = cur
        return OrderList(orders=orders, starting_cash=NOTIONAL), CleanData(frames={"close": cdf})

NAME, KIND, PRESET = "BTC SMA(5/20)", "order_book", "binance_um_perpetual"
DESCRIPTION = "Single-asset BTC SMA crossover, long/short."
```

### 4.4 Running a backtest — parameters

All three kinds run the same way: build a `bundle`, then call `run_backtest`.

```python
from framework import evaluate_alpha
from backtest import run_backtest, nav_fig
bundle = evaluate_alpha({"alpha_cls": Alpha, "kind": KIND, "name": NAME, "preset": PRESET})
res = run_backtest(bundle, start="2021-01-01", end=None, emit_orders=True)
print(repr(res)); nav_fig(res).show()
```

`run_backtest` signature:

```python
run_backtest(bundle, *, start=None, end=None,
             buy_bp=None, sell_bp=None, slip_bp=None, emit_orders=False)
```

| Parameter | Default | What it does |
|---|---|---|
| `bundle` | required | The dict from `evaluate_alpha({...})` — carries your kind, weights/orders, close, preset. |
| `start` | `None` | Backtest start date. Accepts `"2021-01-01"`, `"20210101"`, a `pd.Timestamp`, or `None` (= from the first available date). |
| `end` | `None` | End date, same formats. `None` = through the latest available date. |
| `buy_bp` | `None` | Override the **buy** cost (basis points). `None` = use the preset (5 bp). Set `0` to see gross. |
| `sell_bp` | `None` | Override the **sell** cost (bp). `None` = preset (5 bp). |
| `slip_bp` | `None` | Override **slippage** (bp). `None` = preset (5 bp). |
| `emit_orders` | `False` | Weight kinds only: also return the executable BUY/SELL order stream on `res.orders`. |

**Cost-override precedence:** your `buy_bp/sell_bp/slip_bp` kwargs > the alpha's `cost_overrides` > the preset. The `binance_um_perpetual` preset is **5 bp fee + 5 bp slippage per side**, `initial_cash = 10_000`, annualization `365` (crypto trades 7 days/wk). **Submissions must use the preset as-is** — overrides are for your own exploration only (`rules.md`).

**Gross vs. net** — to separate signal quality from cost drag, run with zero cost:
```python
net   = run_backtest(bundle, start="2021-01-01")
gross = run_backtest(bundle, start="2021-01-01", buy_bp=0, sell_bp=0, slip_bp=0)
print("NET  :", repr(net))
print("GROSS:", repr(gross))    # if gross is great but net is flat → your turnover is too high
```

**Reading the result** (`res`):
```python
res.summary()      # dict of ~20 metrics (sharpe, max_drawdown, cagr, ann_turnover, …)
res.nav            # NAV series           res.returns   # daily net returns
res.turnover       # daily |Δweight|      res.cost      # daily cost paid
res.funding        # daily funding PnL (weight kinds)
res.orders         # executable orders (when emit_orders=True)
```
Charts: `from backtest import nav_fig, drawdown_fig, turnover_fig, cost_fig` → `nav_fig(res).show()`. One-page HTML: `from backtest import to_html; to_html(res, "report.html", title=NAME)`. Compare alphas: `from backtest import compare; compare({"Mine": r1, "BTC hold": r2})`.

Full contract and more depth: `alpha_anatomy.md`. Starters: `templates/`.

---

## 5. Viewing data in the dash

Open the dash (http://localhost:8050) and click the **Data Monitor** tab. It's a
**read-only inventory of what's cached on your machine** (`~/njt-contest/data-cache/feeds/`):

- **Status** — `OK` = cached, `—` = not fetched yet.
- **Name** — human asset name, e.g. `Bitcoin (BTC)` (see §6).
- **identity / intervals / rows / first / last / size** — which intervals you have for that symbol, the row count, and the date range.

Two things to know:
- The table is a **snapshot taken when the container booted.** If you fetch or
  extract data **after** the dash is already up, click **Refresh** on the Data
  Monitor (or `docker compose restart njt`) to re-scan — otherwise it still shows
  the boot-time state.
- The Data Monitor **only views** cache status — it never downloads. Manage data
  from a Jupyter cell (`update_cache()`, `fetch_all_1d()`, `Dataset.load(update=…)`).

The real proof your data is loaded is in Jupyter:
```python
Dataset.load("binance.klines.um.Close.1d", pandas=True, holdout_recent=False).shape  # (T, ~500+)
```

---

## 6. Searching by Name

The Data Monitor's **Name** column shows readable names (`Bitcoin (BTC)`,
`Tether Gold (XAUT)`, …) so you don't have to recognize raw tickers like
`xautusdt`. The table's filter row is **case-insensitive** — type into the box
under any column header to narrow the rows:

- Type `bitcoin` (or `BTC`, or `btc`) under **Name** → just Bitcoin.
- Type `tether` → Tether-family names (USDT, Tether Gold, …).
- Type `1d` under **intervals**, or `OK` / `—` to filter by cache status.

Filtering is purely a view over the table; it doesn't fetch or change anything.

---

## 7. Seeing others' submissions

The dash's **Strategy dropdown** lists everything under
`njt-submissions/interns/`. Because the dash reads the filesystem, what you see
depends on what's in your local `njt-submissions` checkout:

1. **Your own alphas show immediately** — the moment you `submit()`, the files
   are written into `njt-submissions/interns/<your-handle>/…`, so they appear in
   the dropdown (even before the admin merges your PR).
2. **To see peers' merged alphas**, pull the canonical `main` (you stay on `main`
   — no branch checkout):
   ```bash
   cd ~/njt-contest/njt-submissions
   git pull origin main
   ```
   The container's `/submissions` reflects the host instantly (same files). The
   dropdown auto-refreshes within ~30s (it polls for new submissions); if a
   freshly-pulled alpha doesn't show, `docker compose restart njt` and refresh
   the tab.

Strategies are grouped in the dropdown — built-in **benchmarks** (BTC buy-hold,
MAJORS_9 equal-weight, …) vs. **submissions** (`<handle> · <name>`). Pick two and
the dash overlays their NAV / drawdown / stats so you can compare your alpha
against a benchmark or a peer's.

> Reminder: you no longer check out `interns/<handle>`. Set your handle once in
> `~/njt-contest/.env` (`NJT_HANDLE=<your-handle>`), keep `njt-submissions` on
> `main`, and `submit()` pushes to your branch on its own.
