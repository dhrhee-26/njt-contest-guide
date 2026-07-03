# NJT Contest — Intern Guide

You design crypto alpha strategies, and everyone's results are compared in a shared dash UI. Your `interns/<handle>` branch on `njt-submissions` **is** your workspace — code and results live together there, and you push directly to it. No PR, no admin merge; code is visible to your fellow interns by design (this is Phase 2 — see `rules.md` §0 if you're coming from Phase 1's PR-based, code-hidden model).

---

## End-to-end flow

```
Setup  →  Write alpha  →  Local backtest  →  submit() (commit + push your branch)  →  sync_peers.sh: compare in dash
```

The contest exposes you to **one Docker image + one git repo**:

| Thing | Your role |
|---|---|
| **`ghcr.io/dhrhee-26/njt-dash`** (Docker image, public) | A container with the SDK + dash + Jupyter Lab pre-installed. One `docker pull`. |
| **`dhrhee-26/njt-submissions`** (git repo) | Your `interns/<handle>` branch is your whole workspace — check it out and it's mounted straight into the container. `submit()` pushes there directly. |
| **`njt-sdk` / `njt-dash`** (public source) | Not baked-in-only anymore — feel free to read the source if you (or your agent) want to understand the engine internals. |

---

## 1. Setup (one-time, ~5 minutes)

Prerequisites:
- **Docker Desktop** (https://www.docker.com/products/docker-desktop/) — no Python, pip, or virtualenv setup required
- **SSH key registered with GitHub** — the container pushes your submissions via SSH; the same key clones your private submissions branch on the host (see `setup.md` Part 3)

> **New to Docker / the command line?** Read [`setup.md`](./setup.md) instead — every step spelled out, including installing Docker Desktop, configuring Git + SSH, and walking through your first backtest + submission. Come back here once everything works.

```bash
# 1.1 Clone this guide repo into ~/njt-contest.
#     It contains docker-compose.yml, the docs, the templates, and
#     reference starters at my-alphas/*.py (copy whichever you like below).
git clone https://github.com/dhrhee-26/njt-contest-guide.git ~/njt-contest
cd ~/njt-contest

# 1.2 Clone the submissions repo (SSH — private) as `workspace`, and check
#     out YOUR branch directly. This IS your workspace from here on.
git clone git@github.com:dhrhee-26/njt-submissions.git workspace
cd workspace && git checkout interns/<your-name> && cd ..

# 1.3 (optional) start from a reference alpha instead of a blank file
cp my-alphas/my_first_alpha.py workspace/my_first_alpha.py
```

`<your-name>` is the handle the admin gives you (ask them to create
`interns/<your-name>` on `njt-submissions` if the checkout fails).

Resulting folder layout:

```
~/njt-contest/                                  ← cloned from njt-contest-guide
├── docker-compose.yml                          ← container config (image, ports, mounts)
├── README.md / setup.md / ...                  ← these guide docs
├── templates/                                  ← reference template alphas
├── my-alphas/                                  ← reference starters (copy from here, not mounted)
│   ├── my_first_alpha.py                       ← target_weight starter (cross-sectional, 2 assets)
│   ├── my_first_order_book_alpha.py            ← order_book starter (event-driven, single asset)
│   ├── funding_order_book_alpha.py             ← order_book example using the funding rate
│   ├── universe_momentum_alpha.py              ← target_weight over the liquid universe (panel)
│   └── breakout_order_book_alpha.py            ← order_book Donchian breakout on a liquid coin
└── workspace/                                  ← YOUR interns/<your-name> branch (mounted as /workspace)
    ├── my_first_alpha.py                       ← your code — organize however you like
    ├── interns/<your-name>/                    ← submit() writes results here (dash-readable)
    └── tools/sync_peers.sh                     ← pulls in everyone else's branch to compare
```

---

## 2. Bring up the container — daily

```bash
cd ~/njt-contest
docker compose up -d            # first run pulls ~1 GB image — ~5 minutes
```

Done. Open in browser:

| URL | What |
|---|---|
| http://localhost:8888 | **Jupyter Lab** — `workspace/` (your branch) is the root, SDK + dash pre-installed |
| http://localhost:8050 | **dash UI** — reads `workspace/`; run `tools/sync_peers.sh` first to see other interns' alphas too |

When done:

```bash
docker compose down             # stop container (files in ~/njt-contest are preserved)
```

Next day: `cd ~/njt-contest && docker compose up -d` and you're back.

---

## 3. First alpha — single-file pattern

In Jupyter Lab (http://localhost:8888), the left sidebar already shows five runnable starters shipped with the guide:

| File | Kind | Default signal | Good fit for |
|---|---|---|---|
| `my_first_alpha.py` | `target_weight` | 10-day cross-sectional momentum on BTC + ETH, long top half / short bottom half | continuous portfolio reweights, cross-sectional ideas |
| `my_first_order_book_alpha.py` | `order_book` | SMA(5/20) crossover on BTC (state machine) | discrete entry/exit decisions, event-driven ideas |
| `funding_order_book_alpha.py` | `order_book` | long BTC while 7d avg funding is positive, else flat | event-driven ideas keyed off funding / non-price data |
| `universe_momentum_alpha.py` | `target_weight` | 30d cross-sectional momentum over **all liquid USDT-perps** (panel + `min_dollar_volume`) | the real cross-section — showcases the whole-universe panel + liquidity gate |
| `breakout_order_book_alpha.py` | `order_book` | Donchian 20/10 breakout on a liquid coin (`liquid_universe`) | trend ideas on any liquid symbol, not just BTC |

Pick whichever style fits your idea and edit it. The walkthrough below uses `my_first_alpha.py`; the order_book file behaves the same way (open, edit signal, Shift+Enter to backtest, optional submit block at the bottom).

### 3.1 Change one signal line

Open `my_first_alpha.py` in Jupyter and find the `# ← write your signal here` marker. Edit that one line.

Example — change 10-day momentum to 60-day:

```python
# Before
signal = close.pct_change(10)
# After
signal = close.pct_change(60)
```

(Want to start over from scratch? Copy `~/njt-contest/templates/target_weight_template.py` over `my_first_alpha.py` — or `templates/order_book_template.py` over `my_first_order_book_alpha.py` — from a host terminal.)

### 3.2 Backtest — paste the whole file into a notebook cell

Create a new `.ipynb` in Jupyter Lab → paste the entire `my_first_alpha.py` into a cell → Shift+Enter:

- `SimulationResult(...)` prints (20 metrics)
- NAV chart renders inline beneath the cell

Or run from Jupyter Lab's Terminal:
```bash
python /workspace/my_first_alpha.py
```

(Inside the container, `/workspace` = host's `~/njt-contest/workspace/` — your `interns/<handle>` branch checkout.)

---

## 4. Alpha structure — the `Alpha` class contract

`framework.evaluate_alpha` only requires one method:

```python
class Alpha:
    def get(self) -> tuple[Positions | OrderList, CleanData]:
        ...
```

- Return **`Positions`** → KIND `"target_weight"` (date × symbol → weight)
- Return **`OrderList`** → KIND `"order_book"` (chronological orders, single-asset)
- **`CleanData(frames={"close": ...})`** always alongside — the `close` key is required

Plus four module-level metadata constants:

```python
NAME        = "My alpha name"            # human-readable label
KIND        = "target_weight"            # | "order_book"
PRESET      = "binance_um_perpetual"     # cost model (only one for now)
DESCRIPTION = "one-line description"
```

Details → [`alpha_anatomy.md`](./alpha_anatomy.md).

---

## 5. Choosing a KIND

| | `target_weight` | `order_book` |
|---|---|---|
| **Mental model** | Cross-sectional / portfolio — daily weights per symbol | Event / state machine — trade only on signal flips |
| **Output** | wide DataFrame (date × symbol → weight) | chronological list of Order objects (single-asset) |
| **Signal examples** | rank, z-score, momentum, mean reversion | SMA crossover, breakout, regime detection |
| **Asset count** | multi-asset (e.g. 9 majors) | single asset |

(A third kind, **`margin_weight`** — the default — runs the same weights statefully with leverage/liquidation/funding; see [`rules.md`](./rules.md) §1.)

**Kind is not gated by week.** Any kind is submittable any week — `submit()` rejects nothing on kind. **W1's deliverable is one weight-based alpha *and* one `order_book` alpha** (see the program plan PDF, the source of truth). Per-week deliverables → [`rules.md`](./rules.md) §1.

---

## 6. Local validation — metrics + dash comparison

### 6.1 Inspect stats / time series directly

```python
print(res.summary())     # dict — 20 metrics
res.nav                  # pd.Series — NAV
res.returns              # pd.Series — daily net return
res.turnover             # pd.Series — daily |Δw|
res.cost                 # pd.Series — daily cost in return units
```

### 6.2 Compare with other alphas in dash — no extra command

dash is already running at http://localhost:8050. Refresh the browser → Strategy dropdown:

- **alpha group** — 11 built-in reference alphas (including `MAJORS_9_EW` benchmark)
- **submission group** — your own submissions, plus everyone else's once you've run `tools/sync_peers.sh` (§8)
- **benchmark group** — 9 majors buy-hold + equal-weight

All evaluated under the same cost preset → fair comparison.

### 6.3 Compare two of your own alphas inside a notebook

```python
from framework import evaluate_alpha
from backtest import run_backtest, compare
from my_alpha_v1 import Alpha as A1
from my_alpha_v2 import Alpha as A2

r1 = run_backtest(evaluate_alpha({"alpha_cls": A1, "kind": "target_weight", "preset": "binance_um_perpetual"}))
r2 = run_backtest(evaluate_alpha({"alpha_cls": A2, "kind": "target_weight", "preset": "binance_um_perpetual"}))

cmp = compare({"v1": r1, "v2": r2})
cmp.results          # dict[name → SimulationResult]
```

For comparison against the built-in benchmarks (MAJORS_9 equal-weight, single-symbol buy-holds), use the dash UI at http://localhost:8050 — select your alpha + one or more benchmarks in the dropdown and click RUN BACKTEST.

---

## 7. Submit — one call from inside Jupyter

Once your alpha is ready, in a notebook cell:

```python
from framework import submit

submit(
    Alpha(),
    strategy_id="rsi_reversion_v1",
    name="14d RSI Mean Reversion",
    preset="binance_um_perpetual",
    description="Cross-sectional RSI(14) reversal on 9 majors.",
)
```

`submit()` runs `export_submission` (writes `positions.parquet` + `meta.json` under `/workspace/interns/<your-handle>/rsi_reversion_v1/`), then `git add -A` — your **whole** workspace, code included, not just that folder — commits, and pushes straight to the branch you're on. No PR, nothing for the admin to merge: pushing to your own branch *is* the submission.

Output looks like:

```
✓ submitted: interns/<your-handle>/rsi_reversion_v1
  commit:    abc1234567  on interns/<your-handle> (pushed)
```

You must already be checked out on `interns/<your-handle>` for this to work (Part 1.2 above) — `submit()` refuses to push if you're on some other branch.

### 7.1 What if nothing changed?

`submit()` checks whether anything actually changed since your last commit. If not, it prints a message and skips creating an empty commit. Safe to re-run as many times as you want.

---

## 8. See everyone else's alphas — `sync_peers.sh`

There's no merge to pull from anymore — instead, pull each peer's branch in directly:

```bash
cd ~/njt-contest/workspace
./tools/sync_peers.sh              # every active interns/* branch
./tools/sync_peers.sh alice bob    # or just specific handles
```

This checks out each peer's branch read-only alongside yours (as `interns/<peer>/` symlinks — see the script for how) and regenerates `universe.json`. Refresh http://localhost:8050 → their alphas (and code, if you want to look — `cd workspace/interns/<peer>` or browse it in Jupyter Lab's file browser) appear in the submission group of the Strategy dropdown. Re-run it any time to pick up their latest pushes.

---

## 9. Cache management — the data lives on your machine

Every backtest downloads Binance data once and caches it as a parquet file. The cache is a normal folder **on your own computer**, bind-mounted into the container, so it **persists across `docker compose down` / `up`** — you only pay the download cost the first time you touch a symbol.

| Where you look | Path |
|---|---|
| **Your computer** (host) | `~/njt-contest/data-cache/feeds/` |
| Inside the container | `/home/njt/.cache/feeds/` |

Same files, two views. One parquet per identity, e.g. `binance.klines.um.btcusdt.1d.parquet`, `binance.fundingrate.um.btcusdt.parquet`. The folder grows as you backtest more symbols / intervals.

**See what's cached**

- **dash Data Monitor tab** (http://localhost:8050) — a read-only inventory of which identities/intervals are cached (`OK`) vs `missing`. View only; manage with the methods below.
- Finder (macOS): `Cmd + Shift + G` → `~/njt-contest/data-cache/feeds` → browse the parquet files. (File Explorer on Windows: `%USERPROFILE%\njt-contest\data-cache\feeds`.)
- Terminal: `ls -lh ~/njt-contest/data-cache/feeds/` · total size `du -sh ~/njt-contest/data-cache/feeds/`.

> The Jupyter file browser is rooted at `my-alphas/`, so it does **not** show the cache — use Finder/Explorer or the terminal.

**Refresh / update a symbol** — pass a parameter to `Dataset.load`, no button needed:

```python
Dataset.load("binance.klines.um.btcusdt.1d", update=True,     holdout_recent=False)  # force a full re-fetch
Dataset.load("binance.klines.um.btcusdt.1d", update="append", holdout_recent=False)  # fetch only data newer than the cache
```

**Delete** — just remove the parquet (Finder → trash, or `rm`); it is re-downloaded on the next backtest that needs it. No container restart required.

```bash
rm ~/njt-contest/data-cache/feeds/binance.klines.um.btcusdt.1d.parquet   # one identity
rm -rf ~/njt-contest/data-cache/feeds/                                   # clear everything
```

**Bulk — the shipped seed + keeping it current**

You don't have to fetch the whole universe yourself. A **seed cache** of klines for *every* USDT-perp is published on the guide repo's [Releases](https://github.com/dhrhee-26/njt-contest-guide/releases) so everyone starts from the same data with no minutes-per-symbol wait. Two matched tarballs — **1d** (for backtests) and **1h** (for `margin_weight` intraday liquidation) — download both once:

```bash
cd ~/njt-contest
curl -L -o seed-cache-1d.tar.gz https://github.com/dhrhee-26/njt-contest-guide/releases/latest/download/seed-cache-1d.tar.gz
curl -L -o seed-cache-1h.tar.gz https://github.com/dhrhee-26/njt-contest-guide/releases/latest/download/seed-cache-1h.tar.gz
tar -xzf seed-cache-1d.tar.gz -C data-cache/      # → data-cache/feeds/*.parquet  (~35 MB)
tar -xzf seed-cache-1h.tar.gz -C data-cache/      # 1h klines for liquidation       (~800 MB)
```

> The **1h** seed is what lets `margin_weight` judge liquidation intraday (a wick that breaches mid-day liquidates at that hour, not just at the close). It's optional but recommended — without it, liquidation falls back to the daily high/low, then the close; nothing breaks either way. The 1d and 1h seeds cover the same symbols and dates.

Then keep it current yourself — from a Jupyter cell:

```python
from feeds import update_cache, fetch_all_1d

update_cache()      # incrementally bring every cached symbol up to today (parallel)
fetch_all_1d()      # also pull any newly-listed USDT-perp 1d you don't have yet
```

- `update_cache()` only downloads data *newer* than your cache (append) — refreshing the whole seed is minutes, not the hours a cold fetch would take.
- New coins also appear as **missing** in the dash Data Monitor; `fetch_all_1d()` (or `Dataset.load("binance.klines.um.<sym>.1d")`) grabs them.
- **Intraday is opt-in, per symbol** — `Dataset.load("binance.klines.um.solusdt.1h", update=True, holdout_recent=False)`. 1m for the whole universe is multiple GB, so only fetch the symbols you actually need.

**Whole-universe panel** — load one field across *every cached symbol* at once, as a wide DataFrame (columns = symbol, index = datetime) — ideal for cross-sectional alphas:

```python
close = Dataset.load("binance.klines.um.Close.1d", pandas=True, holdout_recent=False)
# close.shape -> (dates, ~530 symbols); close["btcusdt"], close[["btcusdt","xautusdt"]], ...

# liquidity-gated in one call — drop thin symbols (same $-volume gate as rules.md §2.1):
liquid_close = Dataset.load("binance.klines.um.Close.1d", pandas=True, holdout_recent=False,
                            min_dollar_volume=10_000_000)   # ~184 symbols
```

The capitalised field is `Open` / `High` / `Low` / `Close` / `Volume`. It reads only what's cached (extract the seed first), and symbols with different listing dates are NaN-padded.

---

## 10. Image updates

When the admin announces a new SDK / dash version (Slack etc.):

```bash
cd ~/njt-contest
docker compose pull                      # fetch the new image
docker compose up -d --force-recreate    # swap the running container to it (~30 seconds)
```

`docker compose pull` alone does **not** switch a container that is already running — without `--force-recreate` (or `docker compose down && docker compose up -d`) you stay on the old image. Your notebooks / alpha files / submissions / cache are all mounted, so the update doesn't touch them.

---

## 11. Common gotchas

Details → [`rules.md`](./rules.md). The big ones:

1. **`Dataset.load(...)` defaults to `holdout_recent=True`** — silently trims the last 30 days. For backtest code, always pass `holdout_recent=False`.
2. **`weights` is decision-time** — do NOT call `.shift(1)` yourself; the engine handles it.
3. **Symbol names are lowercase USDT-perp** — `btcusdt`, `ethusdt`, ... (not `BTC`, `BTC/USDT`, or uppercase).
4. **Typo'd / non-existent symbols** — the universe is any Binance USDT-perp (`rules.md` §2), but the exact form is lowercase `<base>usdt`; spot-only tokens / other quotes won't fetch.
5. **`cost_overrides` in `meta.json` is forbidden** — zeroing costs to inflate Sharpe is a fairness violation.
6. **`submissions_root` is `/workspace`** — in-container path. Auto-syncs with host's `~/njt-contest/workspace` (your `interns/<handle>` branch).
7. **You must be on `interns/<handle>`, not `main`** — `submit()` refuses to push otherwise (Phase 2; Phase 1 used to want you on `main`).

---

## 12. Where to go next

| Doc | Covers |
|---|---|
| [`setup.md`](./setup.md) | Detailed setup walkthrough for first-time users (Docker install, Git config, first alpha, first submission) |
| [`alpha_anatomy.md`](./alpha_anatomy.md) | Alpha contract details, per-KIND construction, modular vs inline |
| [`rules.md`](./rules.md) | Contest rules, per-week constraints, gotcha checklist |
| [`templates/target_weight_template.py`](./templates/target_weight_template.py) | Cross-sectional alpha starter |
| [`templates/order_book_template.py`](./templates/order_book_template.py) | Event-driven alpha starter |

Questions → admin or #njt-contest channel.
