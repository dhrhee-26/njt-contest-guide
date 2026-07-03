# Phase 2 is live — how you work from here

Phase 2 has started. Two things change: **your environment** (no more Docker or Jupyter — you now work in a local Python environment) and **how you share** (code is open now, and you push straight to your own branch). Please read this once and do the setup below.

---

## ⚡ Action required first — push your Phase 1 work so everyone can see it

**As soon as possible, push your final portfolio and every underlying alpha — the actual source code — to your `interns/<your-handle>` branch.**

In Phase 1 you only ever submitted `positions.parquet` / `meta.json`; your `.py` code stayed on your own machine. Phase 2 is the opposite — **code is meant to be read by your peers.** So the first thing to do after the re-setup below is:

1. Move your Phase 1 strategy files (your final portfolio + the component alphas) into your `workspace/` folder.
2. Run each one so it writes its result, then submit it (this commits the code *and* the result to your branch).
3. Confirm they show up in dash and that your branch on GitHub now contains the `.py` files.

Do this **early** — the peer-review and agent work depends on everyone being able to read each other's Phase 1 strategies. Don't wait until the last minute.

---

## What's new in Phase 2

- **Code is shared.** Everyone can read everyone's strategy code — by design. `njt-sdk` and `njt-dash` are public now too, so you (and the agents you'll build) can read the engine internals.
- **No PRs, no merges.** Your `interns/<your-handle>` branch *is* your workspace. `submit()` commits and pushes straight to it — pushing **is** the submission. Nothing for an admin to merge.
- **No Docker, no Jupyter.** You now run everything in a normal local Python environment. This is so you can `pip install` anything your agent system needs later, without waiting on us to rebuild an image.

---

## One-time re-setup (~10 minutes)

Full step-by-step is in `setup.md` (do `git pull` in `~/njt-contest` first to get the latest). Short version:

**0. Install Python 3.13** if you don't have it — check with `python3 --version`.
- Mac: `brew install python@3.13`
- Windows: installer from https://www.python.org/downloads/ (tick **"Add python.exe to PATH"**)
- (Python 3.13 specifically — some packages don't have prebuilt wheels for 3.14 yet.)

**1. Update the guide and drop the old Docker setup**
```bash
cd ~/njt-contest && git pull
docker compose down          # then you can quit / uninstall Docker Desktop — no longer needed
```

**2. Your branch becomes your workspace**
```bash
git clone git@github.com:dhrhee-26/njt-submissions.git workspace
cd workspace && git switch interns/YOUR-HANDLE && cd ..
```
(Use `git switch`, not `git checkout` — see `setup.md` if it complains.)

**3. Create a virtual environment and install the SDK + dash**
```bash
python3 -m venv .venv && source .venv/bin/activate       # Windows: .venv\Scripts\Activate.ps1
pip install "njt-sdk @ git+https://github.com/dhrhee-26/njt-sdk.git" "njt-dash @ git+https://github.com/dhrhee-26/njt-dash.git"
```

**4. Move your Phase 1 code into `workspace/`** (see the Action item at the top) and submit it.

---

## Daily workflow — two terminal tabs

```bash
# Tab 1 — dash, leave it running
cd ~/njt-contest && source .venv/bin/activate && njt-dash --submissions workspace   # → http://localhost:8050

# Tab 2 — write and run your code
cd ~/njt-contest/workspace && source ../.venv/bin/activate
code .                    # edit in VS Code (or any editor)
python3 my_alpha.py       # run a backtest
```

**The research loop:** write a signal in a `.py` file → `python3 <file>` → read Sharpe / drawdown / turnover → tweak → run again. When a version is worth keeping, add a `submit(...)` call and run it — it pushes to your branch and appears in dash within ~30 seconds.

**A strategy is just a `.py` file with an `Alpha` class** (three blocks: Data → Signal → Position). There's a full "write one from scratch" example in `setup.md` Part 6.5, the contract is in `alpha_anatomy.md`, and copy-paste starters are in `templates/`.

**Submit:**
```python
from framework import submit
submit(Alpha(), strategy_id="my_alpha_v1", name="...", preset="binance_um_perpetual", description="...")
```

**See everyone else's work:**
```bash
cd ~/njt-contest/workspace && ./tools/sync_peers.sh
```
This pulls each peer's branch into `workspace/peers/<handle>/` (their code and results) and adds their strategies to dash. Open `peers/<handle>/` in your editor to read their code.

---

## Reminders

- You must be on your own branch (`interns/YOUR-HANDLE`), not `main`, for `submit()` to work.
- Don't delete old strategy versions — use a new `strategy_id` (`_v2`, `_v3`) so your progression stays visible.
- Never paste a GitHub token, password, or your SSH private key into any chat or AI assistant. Nothing here needs them.

Questions → this channel or DM me.
