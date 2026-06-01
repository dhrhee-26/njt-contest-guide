# NJT Contest — Intern Guide

You design crypto alpha strategies, and everyone's results are compared in a shared dash UI. Your alpha source code stays on your own machine — only the **results** (positions) are submitted via PR.

---

## End-to-end flow

```
Setup  →  Write alpha  →  Local backtest  →  export_submission  →  PR  →  After merge: compare in dash
```

The contest only exposes you to **one Docker image + one git repo**:

| Thing | Your role |
|---|---|
| **`ghcr.io/dhrhee-26/njt-sdk-dist`** (Docker image, public) | A container with the SDK + dash + Jupyter Lab pre-installed. One `docker pull`. |
| **`dhrhee-26/njt-submissions`** (git repo) | Where you push your `positions.parquet + meta.json` via PR. Also where you pull other interns' merged submissions from. |
| (SDK source / dash code / agent / etc.) | You don't need to look at these — all baked into the image. |

---

## 1. Setup (one-time, ~5 minutes)

Prerequisites:
- **Docker Desktop** (https://www.docker.com/products/docker-desktop/) — no Python, pip, or virtualenv setup required
- **SSH key registered with GitHub** — the container pushes your submissions via SSH; the same key clones your private submissions branch on the host (see `setup.md` Part 3)

> **New to Docker / the command line?** Read [`setup.md`](./setup.md) instead — every step spelled out, including installing Docker Desktop, configuring Git + SSH, and walking through your first backtest + submission. Come back here once everything works.

```bash
# 1.1 Clone this guide repo into ~/njt-contest.
#     It contains docker-compose.yml, the docs, the templates, and a
#     ready-to-run starter at my-alphas/my_first_alpha.py.
git clone https://github.com/dhrhee-26/njt-contest-guide.git ~/njt-contest
cd ~/njt-contest

# 1.2 Clone the submissions repo (SSH — private) + switch to your branch
git clone git@github.com:dhrhee-26/njt-submissions.git
cd njt-submissions
git checkout interns/<your-name>           # admin creates this branch ahead of time
cd ..
```

`<your-name>` is the handle the admin gives you. If your branch doesn't exist yet, ping the admin.

Resulting folder layout:

```
~/njt-contest/                                  ← cloned from njt-contest-guide
├── docker-compose.yml                          ← container config (image, ports, mounts)
├── README.md / setup.md / ...                  ← these guide docs
├── templates/                                  ← reference template alphas
├── my-alphas/                                  ← your alpha files (mounted into the container as /workspace)
│   ├── my_first_alpha.py                       ← target_weight starter (cross-sectional, 2 assets)
│   ├── my_first_order_book_alpha.py            ← order_book starter (event-driven, single asset)
│   └── funding_order_book_alpha.py             ← order_book example using the funding rate
└── njt-submissions/                            ← cloned submissions repo (mounted as /submissions)
    └── interns/<your-name>/                    ← your submissions accumulate here
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
| http://localhost:8888 | **Jupyter Lab** — `my-alphas/` is the root, SDK + dash pre-installed |
| http://localhost:8050 | **dash UI** — auto-detects submissions, compare your alpha against others |

When done:

```bash
docker compose down             # stop container (files in ~/njt-contest are preserved)
```

Next day: `cd ~/njt-contest && docker compose up -d` and you're back.

---

## 3. First alpha — single-file pattern

In Jupyter Lab (http://localhost:8888), the left sidebar already shows three runnable starters shipped with the guide:

| File | Kind | Default signal | Good fit for |
|---|---|---|---|
| `my_first_alpha.py` | `target_weight` | 10-day cross-sectional momentum on BTC + ETH, long top half / short bottom half | continuous portfolio reweights, cross-sectional ideas |
| `my_first_order_book_alpha.py` | `order_book` | SMA(5/20) crossover on BTC (state machine) | discrete entry/exit decisions, event-driven ideas |
| `funding_order_book_alpha.py` | `order_book` | long BTC while 7d avg funding is positive, else flat | event-driven ideas keyed off funding / non-price data |

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

(Inside the container, `/workspace` = host's `~/njt-contest/my-alphas/`.)

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
| **Contest W1** | ✅ allowed | ❌ |
| **Contest W2** | ❌ | ✅ allowed |

**W1 interns**: target_weight only. **W2 interns**: order_book only.

(Per-week rules → [`rules.md`](./rules.md))

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
- **submission group** — your own + merged submissions from other interns (after §8)
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

`submit()` runs `export_submission` (writes `positions.parquet` + `meta.json` under `/submissions/interns/<your-handle>/rsi_reversion_v1/`), then `git add` / `commit` / `push`, then prints the PR-creation URL. Your handle is auto-detected from the current branch (`interns/<your-handle>`).

Output looks like:

```
✓ submitted: interns/<your-handle>/rsi_reversion_v1
  commit:    abc1234567  on branch interns/<your-handle>
  open PR:   https://github.com/dhrhee-26/njt-submissions/compare/main...interns/<your-handle>?expand=1
```

### 7.1 Open the PR

Click the printed URL. GitHub opens the "Comparing changes" page; click **Create pull request**, then **Create pull request** again to submit. The admin then reviews + updates `universe.json` + merges.

If you push again to the same branch (any new `submit()` call), GitHub updates the open PR automatically — no need to open a new one.

### 7.2 What if positions are unchanged?

`submit()` checks whether anything actually changed since the last push. If your positions are byte-identical to the previous submission, it prints "positions unchanged — nothing to commit" and skips the push. Safe to re-run as many times as you want.

---

## 8. After merge — see your alpha alongside everyone else's

From the host terminal (or Jupyter Terminal):

```bash
cd ~/njt-contest/njt-submissions
git checkout main
git pull origin main
```

Once the host's `njt-submissions/` updates, the container's `/submissions` reflects it instantly (same files, no copy). **No container restart needed.**

Refresh http://localhost:8050 → other interns' alphas appear in the submission group of the Strategy dropdown.

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
4. **Typo'd / delisted symbols** — anything outside `universe.json`'s 9 majors won't fetch. PRs fail review.
5. **`cost_overrides` in `meta.json` is forbidden** — zeroing costs to inflate Sharpe is a fairness violation.
6. **`submissions_root` is `/submissions`** — in-container path. Auto-syncs with host's `~/njt-contest/njt-submissions`.

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
