# Alpha Anatomy — how to write an alpha (in depth)

Read this after the quickstart in `README.md` when you want more depth.

---

## 1. The contract — what `Alpha.get()` must return

`framework.evaluate_alpha(spec)` calls exactly one method:

```python
class Alpha:
    def get(self) -> tuple[Positions | OrderList, CleanData]:
        # All your alpha logic lives here
        ...
```

The return is two dataclasses:

```python
from framework.types import CleanData, Positions, OrderList

@dataclass(frozen=True)
class CleanData:
    frames: dict[str, pd.DataFrame]    # must contain a "close" key

@dataclass(frozen=True)
class Positions:                        # for target_weight
    weights: pd.DataFrame               # date × symbol → weight ∈ [-1, +1]

@dataclass(frozen=True)
class OrderList:                        # for order_book
    orders: list                        # chronological Order objects
    starting_cash: float = 10000.0
```

The `Order` object is duck-typed — it just needs `timestamp / side / qty / price` fields. Define one locally (single-file pattern) or import the shared `strategies.modules.position.state_machine_orders.Order`.

---

## 2. Module-level metadata

```python
NAME        = "60d Momentum Top-3 Long"             # label shown in dash dropdown
KIND        = "target_weight"                       # | "order_book"
PRESET      = "binance_um_perpetual"                # cost model
DESCRIPTION = "one-line description"
```

dash walks each alpha file and registers it in the dropdown based on these four constants. **All four must be present at module level** for dash to recognize the file as an alpha.

Optional:
- `CATEGORY = "alpha"` (default — can omit). `"portfolio"` also valid — for meta-alphas that stack sub-alpha NAVs.
- `Alpha.cost_overrides = {"buy_cost_bp": 0.0}` — class variable. Forbidden in contest submissions (see `rules.md`).

---

## 3. Writing each KIND

### 3.1 `target_weight` — cross-sectional / portfolio

**Example — 60-day cross-sectional momentum long/short:**

```python
from feeds import Dataset
import pandas as pd
from framework.types import CleanData, Positions

SYMBOLS  = ["btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt",
            "adausdt", "dogeusdt", "avaxusdt", "linkusdt"]
LOOKBACK = 60


class Alpha:
    def get(self):
        # 1. Data — wide DataFrame (date × symbol)
        close = pd.concat({
            sym: Dataset.load(f"binance.klines.um.{sym}.1d",
                              pandas=True, holdout_recent=False)["Close"]
            for sym in SYMBOLS
        }, axis=1).dropna(how="any")

        # 2. Signal — 60-day return
        signal = close.pct_change(LOOKBACK)

        # 3. Position — cross-sectional rank → long top half, short bottom half
        rank = signal.rank(axis=1, pct=True)
        n = close.shape[1]
        half = n / 2
        weights = pd.DataFrame(0.0, index=close.index, columns=close.columns)
        weights[rank > 0.5] = +1.0 / half
        weights[rank <= 0.5] = -1.0 / half

        return Positions(weights=weights), CleanData(frames={"close": close})


NAME, KIND, PRESET = "60d Mom L/S (9 majors)", "target_weight", "binance_um_perpetual"
DESCRIPTION = "Cross-sectional 60d momentum, equal-weight long top half / short bottom half."
```

**Shape rules:**
- `close.shape == (T, N)` — wide, N≥1 symbols
- `weights.shape == (T, N)` — same index / columns as close
- `weights[t]` is decision-time. **Do NOT call `.shift(1)` yourself** — the engine handles that.

**What `weights` values mean:**
- `+0.2` → 20% of NAV long on that symbol that day
- `-0.1` → 10% short
- sum to 1 = 100% long-only; sum to 0 = dollar-neutral L/S

### 3.2 `order_book` — event / state-machine driven

**Example — 5/20 SMA crossover on BTC:**

```python
from dataclasses import dataclass
from typing import Literal
import pandas as pd

from feeds import Dataset
from framework.types import CleanData, OrderList


SYMBOL   = "btcusdt"
FAST, SLOW = 5, 20
NOTIONAL = 10000.0


@dataclass(frozen=True)
class Order:
    timestamp: pd.Timestamp
    side: Literal["BUY", "SELL"]
    qty: float
    price: float
    reason: str


class Alpha:
    def get(self):
        close_df = Dataset.load(f"binance.klines.um.{SYMBOL}.1d",
                                pandas=True, holdout_recent=False)["Close"].to_frame(SYMBOL)
        px = close_df.iloc[:, 0]

        # Signal: fast > slow → +1, fast < slow → -1
        sma_fast = px.rolling(FAST).mean()
        sma_slow = px.rolling(SLOW).mean()
        signal = (sma_fast > sma_slow).astype(int) - (sma_fast < sma_slow).astype(int)

        # State machine
        orders, position, prev_sig = [], 0.0, 0
        for ts, price in px.items():
            cur = int(signal.loc[ts]) if not pd.isna(signal.loc[ts]) else prev_sig
            if cur == prev_sig:
                continue
            if position != 0:
                orders.append(Order(ts, "SELL" if position > 0 else "BUY",
                                    abs(position), price, "close"))
                position = 0.0
            if cur != 0:
                qty = NOTIONAL / price
                orders.append(Order(ts, "BUY" if cur > 0 else "SELL", qty, price, "open"))
                position = qty if cur > 0 else -qty
            prev_sig = cur

        return OrderList(orders=orders, starting_cash=NOTIONAL), CleanData(frames={"close": close_df})


NAME, KIND, PRESET = "BTC SMA(5/20)", "order_book", "binance_um_perpetual"
DESCRIPTION = "Single-asset BTC SMA crossover, long/short."
```

**Shape rules:**
- `close.shape == (T, 1)` — **single-asset only** (exactly 1 column)
- `orders` must be chronologically sorted
- Each `Order.timestamp` must be a value in `close.index`

**State-machine essentials:**
- Trade only when the signal flips (`if cur == prev_sig: continue`)
- Close any existing position before opening a new one (= max 2 fills per flip)
- Costs are applied at fill level (notional × bp)

---

## 4. Single-file (inline) vs Modular

### 4.1 Single-file — the `templates/*_template.py` pattern

Everything (data + signal + position) lives inside `get()`. The only imports from the SDK are the two dataclasses in `framework.types`.

**When to use:**
- One-off signal — not going to be reused in another alpha
- Fast iteration — edit a single file
- Custom indicator (RSI, MACD, regime detector, etc.) — anything not in the shared signal modules

**Examples:** `templates/target_weight_template.py`, `templates/order_book_template.py`

### 4.2 Modular — the pattern used by SDK reference alphas

Compose from building blocks in `strategies.modules.{data,signal,position}.*`. The alpha entry file becomes a 4-line slot assignment:

```python
from strategies.modules.data     import BinanceMajorsClose
from strategies.modules.signal   import NDayLogReturn
from strategies.modules.position import CrossSectionalRank
from framework.types import CleanData, Positions

class Alpha:
    data     = BinanceMajorsClose()                          # 9 majors close
    signal   = NDayLogReturn(lookback=60)                    # 60d log return
    position = CrossSectionalRank(direction="high_long")     # rank → top half long

    def get(self):
        clean = self.data.load()
        sig   = self.signal.compute(clean)
        pos   = self.position.build(sig, clean)
        return pos, clean

NAME, KIND, PRESET = "60d Momentum L/S", "target_weight", "binance_um_perpetual"
DESCRIPTION = "..."
```

**When to use:**
- A building block is shared across multiple alphas (one signal + two position variants = two alphas)
- You want to make a piece easy for someone else to reuse

**Built-in building blocks available in the SDK:**
- `data/`: `BinanceMajorsClose`, `BinanceMajorsCloseFunding`, `BtcClose`, `SingleSymbolClose`
- `signal/`: `NDayLogReturn`, `SMACrossover`, `FundingRollingAvg`, `RollingVolatility`, `CompositeSignal`
- `position/`: `CrossSectionalRank`, `TopKLong`, `StateMachineOrders`, `Identity`

You don't need to write modular alphas. Single-file is the recommended path. Modular is just how the SDK's own reference alphas happen to be written.

---

## 5. Data — `feeds.Dataset.load`

### 5.1 Identity convention

`Dataset.load(identity, pandas=True, holdout_recent=False)` with identities like:

```
binance.klines.um.btcusdt.1d           # USDⓈ-M perpetual, 1-day candles
binance.klines.um.btcusdt.1h           # 1-hour candles (W3+)
binance.fundingrate.um.btcusdt         # funding rate
binance.metrics.um.btcusdt             # OI + long/short ratio (W3+ candidate)
```

For contest W1/W2, only `binance.klines.um.{symbol}.1d` is allowed.

### 5.2 Columns when `pandas=True`

```
['datetime', 'Open', 'High', 'Low', 'Close', 'Volume',
 'close_time', 'quote_asset_volume', 'number_of_trades',
 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore']
```

You'll mostly want the uppercased OHLCV. The index is `open_time` (UTC, tz-naive DatetimeIndex).

### 5.3 ⚠ Always pass `holdout_recent=False`

The default is `True`, which silently trims the last 30 days (an OOS-safe buffer). For backtest code, **always** pass `False`:

```python
Dataset.load(identity, pandas=True, holdout_recent=False)
```

Built-in DataModules (`BinanceMajorsClose` etc.) already do this. The single-file pattern is where it's easy to forget.

---

## 6. Reading backtest results

```python
from framework import evaluate_alpha
from backtest import run_backtest

bundle = evaluate_alpha({"alpha_cls": Alpha, "kind": KIND, "name": NAME, "preset": PRESET})
res    = run_backtest(bundle, start="2021-01-01", end=None)

print(repr(res))
# SimulationResult(return=+xx%, sharpe=+x.xx, max_dd=-xx%, ann_turnover=xxx%)

res.summary()       # dict — 20 metrics
res.nav             # NAV pd.Series
res.returns         # daily net return pd.Series
res.turnover        # daily |Δw| pd.Series
res.cost            # daily cost pd.Series
res.funding         # daily funding PnL pd.Series (target_weight only)
```

**Gross (zero-cost) — to check the signal itself separately from cost impact:**

```python
gross = run_backtest(bundle, start="2021-01-01", end=None,
                     buy_bp=0, sell_bp=0, slip_bp=0)
print("NET  :", repr(res))
print("GROSS:", repr(gross))
```

**Visualization:**

```python
from backtest import nav_fig, drawdown_fig, turnover_fig, cost_fig
nav_fig(res).show()
drawdown_fig(res).show()

# Or a single self-contained HTML page
from backtest import to_html
to_html(res, "report.html", title=NAME)
```

---

## 7. Comparing two alphas

```python
from backtest import compare

bundle1 = evaluate_alpha({"alpha_cls": MyAlpha,        "kind": "target_weight", "preset": "binance_um_perpetual"})
bundle2 = evaluate_alpha({"alpha_cls": BenchmarkAlpha, "kind": "target_weight", "preset": "binance_um_perpetual"})

r1 = run_backtest(bundle1, start="2021-01-01")
r2 = run_backtest(bundle2, start="2021-01-01")

cmp = compare({"Mine": r1, "Benchmark": r2})
cmp.results    # dict[name → SimulationResult]
```

Extend the same pattern for more alphas.

---

## 8. Next — submission

When your alpha is ready → `README.md` §7, §8.
