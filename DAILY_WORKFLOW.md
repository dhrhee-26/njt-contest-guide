# A day of strategy research — the loop, walked through

Setup is done (`setup.md`). This is what a normal working day actually looks like: one idea, followed from "I wonder if…" all the way to a submitted strategy. Copy the rhythm, not the specific alpha.

---

## 1. Start your day (~1 minute)

Two terminal tabs, both with the venv active:

```bash
# Tab 1 — dash. Start it once, leave it running all day.
cd ~/njt-contest && source .venv/bin/activate
njt-dash --submissions workspace                 # → http://localhost:8050

# Tab 2 — your work tab.
cd ~/njt-contest/workspace && source ../.venv/bin/activate
git pull                                         # get anything you pushed from another machine
./tools/sync_peers.sh                            # pull in your peers' latest branches
code .                                            # open the workspace in your editor
```

Now open http://localhost:8050 in the browser. `sync_peers.sh` just put everyone's strategies into that dropdown and their code into `workspace/peers/<handle>/` — glance at what people tried yesterday. Reading a peer's `.py` is a legitimate way to get ideas; that's the point of Phase 2.

---

## 2. Have a hypothesis

Research starts with a sentence you can test, not with code. For example:

> "Momentum works on crypto, but it rewards whatever coin just ran hot and volatile. What if I divide momentum by recent volatility, so I'm long the coins that are trending *cleanly*?"

That's a testable claim. Now turn it into an `Alpha`.

---

## 3. Write it — a new `.py` file in `workspace/`

Create `workspace/risk_adj_mom_v1.py`. Three blocks: **Data → Signal → Position.**

```python
import pandas as pd
from feeds import Dataset
from framework.types import CleanData, Positions

SYMBOLS = ["btcusdt", "ethusdt", "solusdt", "bnbusdt", "xrpusdt",
           "adausdt", "dogeusdt", "avaxusdt", "linkusdt"]      # the 9 majors

class Alpha:
    def get(self):
        # 1. Data
        close = pd.concat(
            {s: Dataset.load(f"binance.klines.um.{s}.1d",
                             pandas=True, holdout_recent=False)["Close"]
             for s in SYMBOLS}, axis=1).dropna(how="any")

        # 2. Signal — the hypothesis, in one place
        mom = close.pct_change(60)                     # 60-day momentum
        vol = close.pct_change().rolling(30).std()     # 30-day realized vol
        signal = mom / vol                             # risk-adjusted momentum

        # 3. Position — long-only, the top-3 cleanest trenders, equal weight
        rank = signal.rank(axis=1, ascending=False)
        w = pd.DataFrame(0.0, index=close.index, columns=close.columns)
        w[rank <= 3] = 1/3
        return Positions(weights=w), CleanData(frames={"close": close})

NAME, KIND, PRESET = "Risk-adjusted momentum", "target_weight", "binance_um_perpetual"
DESCRIPTION = "60d momentum / 30d vol, long-only top-3, equal weight."

if __name__ == "__main__":
    from framework import evaluate_alpha
    from backtest import run_backtest, nav_fig
    bundle = evaluate_alpha({"alpha_cls": Alpha, "kind": KIND, "name": NAME, "preset": PRESET})
    res = run_backtest(bundle, start="2021-01-01", end=None)
    print(repr(res))
    for k, v in res.summary().items():
        print(f"  {k:24s} {v}")
    nav_fig(res).show()
```

---

## 4. Run it and read the result

```bash
python3 risk_adj_mom_v1.py
```

You get a `SimulationResult(...)` line, the 20-metric summary, and a NAV chart in the browser. **Don't just look at return — read the diagnostics:**

- **`sharpe`** — risk-adjusted return. This is the headline. Negative or near-zero → the edge isn't there.
- **`max_drawdown_pct`** — worst peak-to-trough. If it's `-100%` the strategy blew up (ruined); the NAV chart drops to the bottom and flatlines at the point it died.
- **`annual_turnover_pct`** and **`cost_drag_pct`** — how much you're trading and what it costs you. Huge turnover (thousands of %) with a big cost drag is the #1 reason a "good signal" loses money. Compare gross vs net by re-running with `run_backtest(bundle, buy_bp=0, sell_bp=0, slip_bp=0)` — if it's great gross but terrible net, your problem is cost/turnover, not the signal.
- **`hit_ratio_pct`** — fraction of up days. ~50% is normal for a real edge; the money is in the size of wins vs losses, not the count.

**Reading the numbers *is* the research.** The result tells you what to change next.

---

## 5. Iterate — change one thing, re-run

Say the signal looks real gross but net is dragged down by turnover. Common next moves, one at a time:

- **Slow it down** — rebalance less often (e.g. only act every 3 days), or smooth the signal (`signal.ewm(span=7).mean()`) to cut turnover.
- **Change the lookbacks** — `pct_change(60)` → `30` or `90`; see if the edge is robust or you just got lucky on one number.
- **Change the book** — top-3/bottom-3 → top-2, or long-only, or a wider universe (`liquid_universe(min_dollar_volume=10_000_000)` instead of the fixed 9 — see `rules.md` §2).

Edit → save → `python3 risk_adj_mom_v1.py` → read again. This is the whole loop, and you'll go around it many times. Keep the ones that survive as new files (`_v2`, `_v3`) so you can see what helped.

> Watch for **look-ahead**: the engine already shifts your weights by one day, so **don't** `.shift(1)` your weights yourself. And always load with `holdout_recent=False`. Both gotchas are in `rules.md` §4.

---

## 6. Compare in dash before you trust it

Refresh http://localhost:8050. In the Strategies dropdown pick **your alpha + a benchmark** (e.g. `MAJORS_9 equal-weight`, or BTC buy-hold) + maybe a **peer's** strategy, and click **RUN BACKTEST**. Everything is scored under the same cost preset, so it's a fair fight. Look at the NAV overlay, the drawdown overlay, and the yearly / rolling-return panels below — a strategy that only works in one year, or only before costs, shows up here.

---

## 7. Submit when a version is worth keeping

Add a `submit(...)` call and run the file:

```python
from framework import submit
submit(Alpha(), strategy_id="risk_adj_mom_v1",
       name=NAME, preset=PRESET, description=DESCRIPTION)
```

```
✓ submitted: interns/YOUR-HANDLE/risk_adj_mom_v1
  commit:    a1b2c3d4e5  on interns/YOUR-HANDLE (pushed)
```

That one call writes the result, `git add -A`s your **whole** workspace (the `.py` too), commits, and pushes to your branch. No PR. Within ~30 seconds it's in your dash dropdown, and any peer who runs `sync_peers.sh` sees both your result and your code.

**Iterating later?** New idea = new `strategy_id` (`risk_adj_mom_v2_ewm`, `..._v3_wider_universe`). Don't overwrite or delete old versions — your progression is part of the story, and dash shows them side by side.

---

## 8. End of day

Nothing to shut down but dash (`Ctrl+C` in tab 1). Your code and submissions are already pushed. A good habit: keep a short running note (a `NOTES.md` in your workspace, which also gets committed) of what you tried and what the numbers said — future-you and your report will thank you.

---

## Where this is heading (Phase 2)

Everything above is you doing one loop by hand: **hypothesis → code → run → read → tweak → submit.** The Phase 2 mission is to build an **agent** that runs this same loop automatically — generating signal ideas, turning them into `Alpha` classes, backtesting them, and `submit()`-ing the good ones, at scale (100 alphas). So get fluent with the manual loop first: the better you understand what makes *you* keep or kill a strategy, the better the system you'll design to do it. And because you can `pip install` anything into your venv, your agent can use whatever LLM SDK or framework you want.

Questions → the contest channel or DM the admin.
