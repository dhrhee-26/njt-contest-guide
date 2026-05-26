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

Prerequisite: **Docker Desktop** (https://www.docker.com/products/docker-desktop/). No Python, pip, or virtualenv setup required.

> **New to Docker / the command line?** Read [`setup.md`](./setup.md) instead — every step spelled out, including installing Docker Desktop, configuring Git, and walking through your first backtest + submission. Come back here once everything works.

```bash
# 1.1 Clone this guide repo into ~/njt-contest.
#     It contains docker-compose.yml, all the docs, and the templates.
git clone https://github.com/dhrhee-26/njt-contest-guide.git ~/njt-contest
cd ~/njt-contest

# 1.2 Your alpha workspace (becomes Jupyter Lab's root)
mkdir my-alphas

# 1.3 Clone the submissions repo + switch to your branch
git clone https://github.com/dhrhee-26/njt-submissions.git
cd njt-submissions
git checkout interns/<your-name>           # admin creates this branch ahead of time
cd ..
```

`<your-name>` is the handle the admin gives you. If your branch doesn't exist yet, ping the admin.

Resulting folder layout:

```
~/njt-contest/                  ← cloned from njt-contest-guide
├── docker-compose.yml          ← container config (image, ports, mounts)
├── README.md / setup.md / ...  ← these guide docs
├── templates/                  ← starter alpha files
├── my-alphas/                  ← your alpha files (mounted into the container as /workspace)
└── njt-submissions/            ← cloned submissions repo (mounted as /submissions)
    └── interns/<your-name>/    ← your submissions accumulate here
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

In Jupyter Lab (http://localhost:8888), the left sidebar shows `my-alphas/`. Work happens there.

### 3.1 Grab a template

From your **host terminal** (not Jupyter):

```bash
cp ~/njt-contest/templates/target_weight_template.py ~/njt-contest/my-alphas/my_alpha.py
# (For an event-driven alpha later, use templates/order_book_template.py.)
```

Refresh the Jupyter Lab browser tab and `my_alpha.py` appears in the left sidebar.

### 3.2 Change one signal line

Open the downloaded `my_alpha.py` in Jupyter and find the `# ← write your signal here` marker. Edit that one line.

Example — change 10-day momentum to 60-day:

```python
# Before
signal = close.pct_change(10)
# After
signal = close.pct_change(60)
```

### 3.3 Backtest — paste the whole file into a notebook cell

Create a new `.ipynb` in Jupyter Lab → paste the entire `my_alpha.py` into a cell → Shift+Enter:

- `SimulationResult(...)` prints (20 metrics)
- NAV chart renders inline beneath the cell

Or run from Jupyter Lab's Terminal:
```bash
python /workspace/my_alpha.py
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

## 7. Submit — `export_submission` + git push (all from inside Jupyter)

Once your alpha is ready, in a notebook cell:

```python
from framework import export_submission
import subprocess

INTERN      = "<your-name>"
STRATEGY_ID = "rsi_reversion_v1"

# 1) Dump artifacts — submissions_root is the in-container path (/submissions)
folder = export_submission(
    alpha=Alpha(),
    intern=INTERN,
    strategy_id=STRATEGY_ID,
    name="14d RSI Mean Reversion",
    preset="binance_um_perpetual",
    description="Cross-sectional RSI(14) reversal on 9 majors.",
    submissions_root="/submissions",
)
# → /submissions/interns/<your-name>/rsi_reversion_v1/
#   ├── positions.parquet
#   └── meta.json
# (Also appears at host's ~/njt-contest/njt-submissions/interns/... since it's a mount.)

# 2) git add + commit + push — host's ~/.gitconfig + ~/.ssh are mounted ro,
#    so git push uses your existing GitHub credentials with no extra setup.
rel = str(folder.relative_to("/submissions"))
subprocess.run(["git", "-C", "/submissions", "add", rel], check=True)
subprocess.run(["git", "-C", "/submissions", "commit", "-m", f"{INTERN}: add {STRATEGY_ID}"], check=True)
subprocess.run(["git", "-C", "/submissions", "push"], check=True)
print(f"✓ submitted + pushed: {rel}")
```

Running that one cell completes the entire submission flow.

### 7.1 Open the PR

Once the cell above finishes pushing, open the PR via GitHub UI or `gh` CLI. In Jupyter Terminal:

```bash
gh pr create --base main --head interns/<your-name> \
  --title "<your-name>: rsi_reversion_v1" \
  --body "RSI(14) cross-sectional reversal on 9 majors. Local Sharpe ~0.3."
```

Or in your host browser at `https://github.com/dhrhee-26/njt-submissions/pulls` → New PR.

The admin then reviews + updates `universe.json` + merges.

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

## 9. Image updates

When the admin announces a new SDK / dash version (Slack etc.):

```bash
cd ~/njt-contest
docker compose pull             # fetch the new image
docker compose up -d            # restart (~30 seconds)
```

Your notebooks / alpha files / submissions are all mounted, so the update doesn't touch them.

---

## 10. Common gotchas

Details → [`rules.md`](./rules.md). The big ones:

1. **`Dataset.load(...)` defaults to `holdout_recent=True`** — silently trims the last 30 days. For backtest code, always pass `holdout_recent=False`.
2. **`weights` is decision-time** — do NOT call `.shift(1)` yourself; the engine handles it.
3. **Symbol names are lowercase USDT-perp** — `btcusdt`, `ethusdt`, ... (not `BTC`, `BTC/USDT`, or uppercase).
4. **Typo'd / delisted symbols** — anything outside `universe.json`'s 9 majors won't fetch. PRs fail review.
5. **`cost_overrides` in `meta.json` is forbidden** — zeroing costs to inflate Sharpe is a fairness violation.
6. **`submissions_root` is `/submissions`** — in-container path. Auto-syncs with host's `~/njt-contest/njt-submissions`.

---

## 11. Where to go next

| Doc | Covers |
|---|---|
| [`setup.md`](./setup.md) | Detailed setup walkthrough for first-time users (Docker install, Git config, first alpha, first submission) |
| [`alpha_anatomy.md`](./alpha_anatomy.md) | Alpha contract details, per-KIND construction, modular vs inline |
| [`rules.md`](./rules.md) | Contest rules, per-week constraints, gotcha checklist |
| [`templates/target_weight_template.py`](./templates/target_weight_template.py) | Cross-sectional alpha starter |
| [`templates/order_book_template.py`](./templates/order_book_template.py) | Event-driven alpha starter |

Questions → admin or #njt-contest channel.
