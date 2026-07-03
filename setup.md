# Setup Walkthrough — Step by Step

This is the **detailed, beginner-friendly** version of setup. It assumes you're not deeply familiar with the command line and you'd like every step spelled out. Total time: about **20 minutes** the first time.

If you already know what you're doing, the quick version is in [`README.md`](./README.md).

---

## Before you start

You need:

- A computer running **macOS**, **Windows 10/11**, or **Linux**
- A **GitHub account** — sign up free at https://github.com if you don't have one
- About **2 GB** of free disk space
- A working internet connection
- The **handle** the contest admin assigned you (e.g., "alice", "bob") — ask them if you don't know
- **Python 3.13** — Part 1 below walks you through installing it if you don't have it
- **A code editor** — VS Code (https://code.visualstudio.com/) is recommended, but use whatever you're comfortable with

> **Security — never paste credentials into a chat or AI assistant.** Nothing in this contest requires a GitHub Personal Access Token (PAT). Everything is public except the submissions repo, which you access via your own SSH key (set up in Part 3). If any guide, error message, or AI assistant (including ChatGPT, Claude, Cursor, Copilot, etc.) ever tells you to paste a PAT, a password, or the contents of `~/.ssh/id_ed25519` (the **private** key, no `.pub`) to debug something — **stop and message the admin instead**. If you have already pasted one, revoke it immediately at https://github.com/settings/tokens and tell the admin.

---

## Part 1 — Install Python 3.13 (~5 minutes)

Check first whether you already have it:

```bash
python3 --version
```

If you see `Python 3.13.x` (any patch version), skip to **Part 2**. If you see an older version, or `command not found`, install 3.13:

**On Mac:**
- If you have Homebrew: `brew install python@3.13`
- Otherwise: download the macOS installer from https://www.python.org/downloads/ and run it

**On Windows:**
- Download the installer from https://www.python.org/downloads/ and run it. **Check the box "Add python.exe to PATH"** on the first screen — easy to miss, and everything below assumes it's checked.
- Or, in PowerShell: `winget install Python.Python.3.13`

**On Linux:**
- Use your distro's package manager (e.g. `sudo apt install python3.13 python3.13-venv` on Ubuntu 24.04+), or https://www.python.org/downloads/ if your distro's version is older.

Verify:
```bash
python3 --version    # or python3.13 --version if you have multiple versions installed
```

---

## Part 2 — Open the Terminal

The Terminal (a.k.a. shell, command line) is where you type commands.

**Mac:**
- Press **Cmd + Space** → type "Terminal" → press **Enter**
- A black-on-white window opens with a prompt like `you@MacBook ~ %`

**Windows:**
- Click Start → type "PowerShell" → click **Windows PowerShell**
- A blue window opens with a prompt like `PS C:\Users\you>`

**Linux:**
- Look for "Terminal" in your applications, or press **Ctrl + Alt + T**

### Tips for using the Terminal

- **Copy and paste**: select text → `Cmd + C` (Mac) or `Ctrl + C` (Windows/Linux) to copy. To paste into Terminal: `Cmd + V` (Mac), `Ctrl + Shift + V` (Linux), or right-click (Windows PowerShell)
- **Pressing Enter** runs whatever you just typed/pasted
- **Up arrow** brings back the previous command
- If you make a typo, use **left arrow** to move around and **Delete/Backspace** to fix it
- **Tab** auto-completes file/folder names — saves typing

Keep this Terminal window open. You'll use it for several steps, and you'll end up wanting a **second** Terminal tab/window once dash is running (Part 5) — Mac: `Cmd+T` for a new tab; Windows Terminal: `Ctrl+Shift+T`.

---

## Part 3 — Set up Git and SSH for GitHub (~5 minutes)

You'll push your submissions through Git to GitHub. You need:
1. Git installed (usually already there on Mac/Linux; needs install on Windows)
2. Your identity configured (name + email)
3. An **SSH key** registered with GitHub — used for both cloning your private submissions branch and pushing to it

### 3.1 Check Git is installed

```bash
git --version
```

If you see something like `git version 2.43.0`, you're good. Skip to **3.2**.

If you see "command not found":
- **Mac**: a popup will appear: "The 'git' command requires the command line developer tools. Would you like to install the tools now?" — click **Install**. Wait ~5 minutes for it to finish. Then try `git --version` again.
- **Windows**: download Git from https://git-scm.com/download/win and run the installer (accept all defaults). Restart PowerShell. Try `git --version` again.

### 3.2 Configure your Git identity

Replace the placeholders with your real name and email (the email should be the same one you used on GitHub):

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Nothing is printed if successful — that's normal.

### 3.3 Generate an SSH key

First, check whether you already have one:

```bash
ls ~/.ssh/id_ed25519
```

If that prints a path (no "No such file" error), you already have a key — skip to **3.4**.

Otherwise, generate one:

```bash
ssh-keygen -t ed25519 -C "you@example.com"
```

Use the same email you used on GitHub. The command will ask three questions:

1. **"Enter file in which to save the key"** — press **Enter** to accept the default (`~/.ssh/id_ed25519`)
2. **"Enter passphrase"** — press **Enter** to leave empty, or set one if you prefer (you'll type it once per Terminal session)
3. **"Enter same passphrase again"** — press **Enter**

You should see "Your identification has been saved in `~/.ssh/id_ed25519`".

### 3.4 Add the public key to GitHub

Copy the **public** key (the `.pub` file — never share the file without `.pub`) to your clipboard:

**Mac:**
```bash
pbcopy < ~/.ssh/id_ed25519.pub
```

**Linux:**
```bash
cat ~/.ssh/id_ed25519.pub
```
Then select the printed line and copy it.

**Windows (PowerShell):**
```powershell
Get-Content ~/.ssh/id_ed25519.pub | Set-Clipboard
```

Open https://github.com/settings/keys in your browser, click **New SSH key**:

- **Title**: anything memorable, e.g. `njt-contest laptop`
- **Key type**: Authentication Key
- **Key**: paste from clipboard

Click **Add SSH key**.

### 3.5 Test the connection

```bash
ssh -T git@github.com
```

The first time you run this, it will ask:

```
The authenticity of host 'github.com (...)' can't be established.
... Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

Type `yes` and press Enter.

You should then see:

```
Hi <your-github-username>! You've successfully authenticated, but GitHub does not provide shell access.
```

That message — including "does not provide shell access" — means success. If you instead see "Permission denied (publickey)", revisit 3.4 (the key wasn't added to GitHub correctly).

---

## Part 4 — Get the contest files + install the SDK (~5 minutes)

### 4.1 Clone this guide repo into `~/njt-contest`

This repo contains all the documentation (including the file you're reading), the starter templates, and reference starter alphas under `my-alphas/`.

```bash
git clone https://github.com/dhrhee-26/njt-contest-guide.git ~/njt-contest
cd ~/njt-contest
```

The `~` symbol is shorthand for your home folder (`/Users/you` on Mac, `C:\Users\you` on Windows).

Verify the contents:

```bash
ls
```

Expected (in some order):
```
README.md           setup.md
alpha_anatomy.md    rules.md      templates    my-alphas
```

### 4.2 Clone the submissions repo AS your workspace, and switch to your branch

```bash
git clone git@github.com:dhrhee-26/njt-submissions.git workspace
cd workspace
git switch interns/YOUR-HANDLE
cd ..
```

**Replace `YOUR-HANDLE`** with the handle the admin gave you (e.g., `alice`).

Use **`git switch`**, not `git checkout` — `main` already has a real `interns/YOUR-HANDLE/` folder in it (from earlier submissions), which makes plain `git checkout interns/YOUR-HANDLE` ambiguous ("branch or file path?"). `switch` only ever means "branch."

If `git switch interns/YOUR-HANDLE` says *"invalid reference"* or similar, the admin hasn't created your branch yet — ask them to create `interns/YOUR-HANDLE` on `dhrhee-26/njt-submissions`.

This `workspace/` folder — checked out on **your** branch — is where everything happens from now on: your alpha code, your agent code, and (once you submit) your results. It's a normal git repo you can `git add` / `git commit` / `git push` like any other; `submit()` just automates that for you.

### 4.3 Copy the starter alphas into your workspace

```bash
cp my-alphas/*.py workspace/
```

Copies the guide's starter alphas into your workspace. You can also just write a file from scratch instead — nothing depends on these being there.

### 4.4 Create a virtual environment and install the SDK

A **virtual environment** (venv) keeps this project's Python packages separate from anything else on your machine.

```bash
cd ~/njt-contest
python3 -m venv .venv
```

Activate it (you'll do this every time you open a new Terminal for this project — see Part 5):

```bash
# Mac / Linux
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Your prompt should now start with `(.venv)`. Install the SDK + dash:

```bash
pip install "njt-sdk @ git+https://github.com/dhrhee-26/njt-sdk.git" "njt-dash @ git+https://github.com/dhrhee-26/njt-dash.git"
```

This takes a minute or two (pulls in `pandas`, `polars`, `pyarrow`, `dash`, and a few others). Verify it worked:

```bash
python3 -c "from feeds import Dataset; from framework import submit; print('ok')"
```

Expect to see `ok`. If this fails, see Troubleshooting.

### 4.5 Verify the final layout

From inside `~/njt-contest`, run:

```bash
ls
```

Expected (in some order):
```
README.md           setup.md      .venv
alpha_anatomy.md    rules.md      templates    my-alphas    workspace
```

If all of those are there, Part 4 is done.

---

## Part 5 — Run dash (~1 minute)

Open a **second** Terminal tab/window (Part 2's tip), and in it:

```bash
cd ~/njt-contest
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
njt-dash --submissions workspace
```

This starts dash and keeps running in this Terminal tab (leave it open — this is your "server" tab). You should see:

```
Dash is running on http://127.0.0.1:8050/
```

Open http://localhost:8050 in your browser — you should see the dash UI.

**Go back to your first Terminal tab** for everything else (Parts 6+) — that one is for editing/running your own code, this one just keeps dash alive in the background.

---

## Part 6 — Your first alpha (~10 minutes)

### 6.1 Open the workspace in your editor

```bash
code ~/njt-contest/workspace     # VS Code — or open the folder manually in your editor of choice
```

You'll see the starter alphas you copied in Part 4.3:
- `my_first_alpha.py` — `target_weight` pattern (continuous portfolio reweights)
- `my_first_order_book_alpha.py` — `order_book` pattern (discrete entry/exit orders)

### 6.2 Open the starter and skim it

Open `my_first_alpha.py`. It's a short, complete example of a target_weight alpha — fetches BTC + ETH daily close, computes a 10-day cross-sectional momentum signal, ranks and goes long/short.

The walkthrough below uses `my_first_alpha.py`, but everything works identically for `my_first_order_book_alpha.py` if you'd rather start from the event-driven pattern.

(Want to restart from the canonical template? `cp ~/njt-contest/templates/target_weight_template.py ~/njt-contest/workspace/my_first_alpha.py` — or `templates/order_book_template.py` over `my_first_order_book_alpha.py`.)

### 6.3 Run it

Back in your **first** Terminal tab (not the one running dash):

```bash
cd ~/njt-contest/workspace
source ../.venv/bin/activate       # if this tab doesn't already have it active
python3 my_first_alpha.py
```

The first run downloads daily-close data for BTC and ETH from Binance Vision (~1 minute on first invocation, cached afterwards). When it finishes you should see:
1. A printed line like `SimulationResult(return=+27.82%, sharpe=+0.60, ...)`
2. A **Summary** block listing 20 metrics
3. A NAV chart (the starter calls `nav_fig(res).show()`, which opens it in your browser)

Congratulations — you've just run your first backtest.

### 6.4 Now modify the signal

Find the line with the comment `← write your signal here` (it's inside the `Alpha.get()` method). It looks like:

```python
        # 2. Signal — your alpha logic goes here.   ←  write your signal here
        #    Below is the default: 10-day cross-sectional momentum.
        signal = close.pct_change(LOOKBACK)
```

Try changing `LOOKBACK = 10` (defined at the top of the file) to a different value like `LOOKBACK = 60`. Save, then re-run:

```bash
python3 my_first_alpha.py
```

This is the basic loop: **edit signal → save → `python3 <file>` → read the result → iterate.** No notebook, no container — just a Python file you run.

Once you're happy with momentum and want a richer cross-section, expand `SYMBOLS` to the full 9 majors listed in `~/njt-contest/rules.md`.

### 6.5 Write your own strategy from scratch

You don't have to edit the starter — a strategy is just a new `.py` file in `workspace/` with an `Alpha` class. Create `workspace/my_reversal_v1.py`:

```python
import pandas as pd
from feeds import Dataset
from framework.types import CleanData, Positions

SYMBOLS = ["btcusdt", "ethusdt", "solusdt"]

class Alpha:
    def get(self):
        # 1. Data — daily close per symbol, wide (date × symbol)
        close = pd.concat(
            {s: Dataset.load(f"binance.klines.um.{s}.1d",
                             pandas=True, holdout_recent=False)["Close"]
             for s in SYMBOLS},
            axis=1,
        ).dropna(how="any")

        # 2. Signal — YOUR idea goes here (this one: 5-day mean reversion)
        signal = -close.pct_change(5)

        # 3. Position — rank cross-sectionally, long the top half / short the bottom
        rank = signal.rank(axis=1, pct=True)
        w = pd.DataFrame(0.0, index=close.index, columns=close.columns)
        w[rank > 0.5]  = +0.5
        w[rank <= 0.5] = -0.5
        return Positions(weights=w), CleanData(frames={"close": close})

NAME        = "5-day cross-sectional reversal"
KIND        = "target_weight"
PRESET      = "binance_um_perpetual"
DESCRIPTION = "Long recent losers, short recent winners, dollar-neutral."

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

Run it the same way:

```bash
python3 my_reversal_v1.py
```

The three numbered blocks — **Data → Signal → Position** — are the whole contract. `get()` returns `(Positions, CleanData)` and the backtest engine does the rest (it applies the t-1 shift, so don't `.shift(1)` your weights yourself). Full contract details are in [`alpha_anatomy.md`](./alpha_anatomy.md); the copy-paste starters in `templates/` cover `order_book` and portfolio patterns too.

That's the research loop: **write a signal → run → read Sharpe / drawdown / turnover → change the signal → run again.** When a version is worth keeping, submit it (Part 8) and compare it against your earlier versions and your peers in dash.

---

## Part 7 — Compare with built-in alphas in dash

Go to the dash UI tab in your browser: http://localhost:8050 (started in Part 5).

You'll see:
- A **Strategies** dropdown on the upper-left
- A date range picker
- A **RUN BACKTEST** button
- Several charts placeholders

Click the Strategies dropdown. You'll see groups:
- **benchmark** — buy-hold strategies for each major + an equal-weight basket (10 strategies)
- **submission** — your own submissions, plus any peers you've pulled in with `sync_peers.sh` (Part 9) — empty until you submit your first alpha

Select one or two strategies, then click **RUN BACKTEST**. After a few seconds, NAV charts, drawdown, and a statistics table appear. Spend a few minutes exploring.

After you submit your own alpha (next part), it appears under the **submission** group in this same dropdown — no waiting on anyone. Dash auto-polls the filesystem every 30 seconds, so it shows up on its own; refresh the browser tab if it's been a moment.

---

## Part 8 — Submit (your first attempt) (~2 minutes)

When you have an alpha you're happy with, add a submit call at the bottom of the file (or run it separately) — `my_first_alpha.py` already has one, commented out:

```python
from framework import submit

submit(
    Alpha(),
    strategy_id="my_first_alpha_v1",   # folder name on your branch (your choice)
    name="My First Alpha",             # human-readable label shown in dash
    preset="binance_um_perpetual",
    description="Trying out the contest.",
)
```

`submit()` writes `positions.parquet` + `meta.json` under `interns/YOUR-HANDLE/my_first_alpha_v1/`, then `git add -A` (your **whole** workspace — the alpha file too, not just the results folder), commits, and pushes straight to the branch you're on (it must be `interns/YOUR-HANDLE` — that's what you switched to in Part 4.2).

Run it:

```bash
python3 my_first_alpha.py
```

You should see something like:

```
✓ submitted: interns/YOUR-HANDLE/my_first_alpha_v1
  commit:    abc1234567  on interns/YOUR-HANDLE (pushed)
```

That's it — nothing else to do. No PR, nobody to wait on for merge. Restart dash (Part 7's note) and your alpha is in the **submission** group.

### Submitting again later

When you iterate and want to push a new version:

- **Same `strategy_id`** → overwrites your previous submission (a new commit on your branch).
- **New `strategy_id`** (e.g., `my_first_alpha_v2`) → creates a separate folder. Both stay on your branch — you (and anyone syncing your branch) can compare them.

If nothing changed since your last commit, `submit()` says so and skips pushing — no harm in running it again.

---

## Part 9 — See other interns' alphas — `sync_peers.sh`

There's no merge to wait for — pull each peer's branch in yourself, any time:

```bash
cd ~/njt-contest/workspace
./tools/sync_peers.sh              # every active interns/* branch
./tools/sync_peers.sh alice bob    # or just specific handles
```

This checks out each peer's full branch under `workspace/peers/<peer>/` (their code — everything) and regenerates `universe.json`. Restart dash (Part 7's note) — their alphas now show up in the **submission** group too. Open `peers/<peer>/` in your editor to read their actual code. Re-run the script any time to pick up new pushes.

---

## Part 10 — Daily routine

Once setup is done, your daily workflow is:

```bash
# Terminal tab 1 — dash, leave running
cd ~/njt-contest && source .venv/bin/activate && njt-dash --submissions workspace

# Terminal tab 2 — everything else
cd ~/njt-contest/workspace && source ../.venv/bin/activate
code .                              # or however you open your editor
python3 my_alpha.py                 # run/iterate
./tools/sync_peers.sh               # see peers' latest work (optional, any time)
```

No containers to start or stop — just activate the venv (once per new Terminal tab) and go. `Ctrl+C` stops dash when you're done for the day.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `python3 --version` shows an old version (e.g. 3.9) even after installing 3.13 | Multiple Python versions installed, old one still first in PATH | Try `python3.13 --version` explicitly. Use `python3.13 -m venv .venv` in Part 4.4 if so, and re-activate. |
| `pip install "njt-sdk @ git+..."` fails while building `pyarrow` or `polars` from source | Your platform/Python combo doesn't have a prebuilt wheel for that package version | Rare on Mac/Windows/Linux x86_64 or Apple Silicon with Python 3.13. Message the admin with the full error — likely needs a version pin adjustment. |
| `git switch interns/YOUR-HANDLE` says `invalid reference` | The admin hasn't created your branch yet | Ask the admin to create `interns/YOUR-HANDLE` on `dhrhee-26/njt-submissions` |
| `git clone git@github.com:...` says `Permission denied (publickey)` | SSH key isn't registered with GitHub | Revisit **Part 3.4** — make sure the contents of `~/.ssh/id_ed25519.pub` are pasted at https://github.com/settings/keys. Then `ssh -T git@github.com` should print "Hi `<your-username>`!" |
| `submit()` says `you're on branch 'main', not interns/<handle>` | You're not on your branch | `cd ~/njt-contest/workspace && git switch interns/YOUR-HANDLE` |
| `submit()` says `not a git repository` | Running the script from somewhere other than inside `workspace/`, or `workspace/` wasn't cloned | Confirm `~/njt-contest/workspace/.git` exists; run scripts with `cd ~/njt-contest/workspace` first |
| dash doesn't show a submission you just pushed | dash auto-polls every 30s — might just not have ticked yet | Wait ~30s and refresh the browser tab. If it's been minutes, check `submit()` actually printed `pushed` |
| `tools/sync_peers.sh` shows a peer with "no commits yet" | That intern hasn't submitted anything yet | Nothing to fix — re-run the script later |
| `(.venv)` doesn't appear in your prompt after `source .venv/bin/activate` | You're in the wrong folder, or on Windows used the wrong activation command | Confirm you're in `~/njt-contest` (`.venv` should be a sibling folder); Windows PowerShell needs `.venv\Scripts\Activate.ps1`, not the Mac/Linux `source` form |
| PowerShell says running scripts is disabled, when activating the venv | Windows' default execution policy blocks `.ps1` scripts | Run PowerShell as Administrator once: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`, then retry |
| `Alpha is not defined` | Running a snippet that references `Alpha` without it being defined in the same file/session | Make sure the class definition and the code that uses it are in the same script, in order |

If you hit anything not in the table, post in **#njt-contest** or message the admin with:
1. What you were doing (which command)
2. The full error message (copy-paste it, don't paraphrase)
3. Your OS and `python3 --version`

**Do not paste GitHub tokens, passwords, or SSH private keys** into any chat, issue, or AI assistant while debugging. None of the contest tooling needs them — see the security note at the top of this document. If a suggested fix asks you to, route it past the admin first.

---

## What to read next

Now that everything works, the recommended reading order is:

1. [`README.md`](./README.md) — the concise quick reference
2. [`alpha_anatomy.md`](./alpha_anatomy.md) — the Alpha class contract in depth
3. [`rules.md`](./rules.md) — contest rules and pre-submit checklist
4. [`templates/target_weight_template.py`](./templates/target_weight_template.py) — starter for cross-sectional alphas
5. [`templates/order_book_template.py`](./templates/order_book_template.py) — starter for event-driven alphas

Good luck.
