# Setup Walkthrough — Step by Step

This is the **detailed, beginner-friendly** version of setup. It assumes you've never used Docker before, you're not deeply familiar with the command line, and you'd like every step spelled out. Total time: about **30 minutes** the first time.

If you already know what you're doing, the quick version is in [`README.md`](./README.md).

---

## Before you start

You need:

- A computer running **macOS** (Intel or Apple Silicon), **Windows 10/11**, or **Linux**
- The admin password for your computer (you'll install one app)
- A **GitHub account** — sign up free at https://github.com if you don't have one
- About **5 GB** of free disk space
- A working internet connection (you'll download ~1 GB)
- The **handle** the contest admin assigned you (e.g., "alice", "bob") — ask them if you don't know

You do NOT need: Python installed, Anaconda, pip, virtualenv, an IDE, or anything Python-related. Everything Python-related lives inside the Docker container.

> **Security — never paste credentials into a chat or AI assistant.** Nothing in this contest requires a GitHub Personal Access Token (PAT). The Docker image is on a **public** registry (`docker pull` works without `docker login`); the submissions repo is accessed via your own SSH key (set up in Part 3). If any guide, error message, or AI assistant (including ChatGPT, Claude, Cursor, Copilot, etc.) ever tells you to paste a PAT, a password, or the contents of `~/.ssh/id_ed25519` (the **private** key, no `.pub`) to debug something — **stop and message the admin instead**. If you have already pasted one, revoke it immediately at https://github.com/settings/tokens and tell the admin.

---

## Part 1 — Install Docker Desktop (~10 minutes)

Docker Desktop is the app that lets you run containers on your machine. Think of a container as a small, self-contained Linux box with everything pre-installed.

### 1.1 Download

Go to https://www.docker.com/products/docker-desktop/

Click **Download Docker Desktop**. The button auto-detects your OS, but if not, pick:
- **Mac with Apple Silicon (M1/M2/M3/M4)** if your Mac is from 2020 or later
- **Mac with Intel chip** if your Mac is from before 2020
- **Windows** if you're on Windows
- **Linux** if you're on Linux (probably Ubuntu)

Save the file to your Downloads folder.

### 1.2 Install

**On Mac:**
1. Open the downloaded `.dmg` file (double-click it in Downloads)
2. Drag the **Docker** icon to the **Applications** folder when prompted
3. Open the Applications folder (Finder → Applications) and double-click **Docker**
4. macOS will ask "Are you sure you want to open this app?" — click **Open**
5. You may be asked to enter your computer password to install some system extensions — enter it
6. Accept the Docker Subscription Service Agreement
7. Skip the tutorial / sign-in screens (you can click "Skip" or "Continue without signing in")

**On Windows:**
1. Open the downloaded `.exe` installer
2. Click through the installer (accept defaults)
3. When asked, enable the **WSL 2** option
4. After install, restart your computer when prompted
5. After restart, Docker Desktop should start automatically. If not, open it from the Start menu

**On Linux:**
1. Follow the official instructions at https://docs.docker.com/desktop/install/linux-install/ — exact commands vary by distribution

### 1.3 Verify Docker is running

After Docker Desktop is installed and started:

- **Mac**: look for the small **whale icon** 🐳 in the menu bar (top of screen). When the whale stops animating and looks steady, Docker is ready.
- **Windows**: the same whale icon appears in the system tray (bottom right). Wait for it to stop animating.

Then open a **Terminal** (see Part 2 below) and run:

```bash
docker --version
```

You should see something like:

```
Docker version 27.4.0, build bde2b89
```

If you see this, Docker is installed correctly. If you see "command not found" or "Cannot connect to the Docker daemon", check the Troubleshooting section at the bottom.

---

## Part 2 — Open the Terminal

The Terminal (a.k.a. shell, command line) is where you type commands. The Docker tutorials all use it.

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

Keep this Terminal window open. You'll use it for several steps.

---

## Part 3 — Set up Git and SSH for GitHub (~5 minutes)

You'll push your submissions through Git to GitHub. You need:
1. Git installed (usually already there on Mac/Linux; needs install on Windows)
2. Your identity configured (name + email)
3. An **SSH key** registered with GitHub — used for both cloning your private submissions branch and pushing to it (from inside the container)

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

Verify the config file now exists as a regular file (this matters for Part 5 — see the note there):

```bash
test -f ~/.gitconfig && echo "ok: ~/.gitconfig is a file"
```

You should see `ok: ~/.gitconfig is a file`. If you see nothing, the two commands above didn't run — try them again.

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
2. **"Enter passphrase"** — press **Enter** to leave empty (the container needs to use the key without prompting)
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

## Part 4 — Get the contest files (~3 minutes)

### 4.1 Clone this guide repo into `~/njt-contest`

This repo contains the `docker-compose.yml`, all the documentation (including the file you're reading), the starter templates, and reference starter alphas under `my-alphas/`. Cloning it gives you everything in one shot.

```bash
git clone https://github.com/dhrhee-26/njt-contest-guide.git ~/njt-contest
cd ~/njt-contest
```

The `~` symbol is shorthand for your home folder (`/Users/you` on Mac, `C:\Users\you` on Windows).

After `cd`, your Terminal prompt should show `njt-contest` somewhere (e.g., `you@Mac njt-contest %`). This means you're inside that folder.

Verify the contents:

```bash
ls
```

Expected (in some order):
```
README.md           docker-compose.yml    setup.md
alpha_anatomy.md    rules.md              templates    my-alphas
```

### 4.2 Clone the submissions repo AS your workspace, and check out your branch

```bash
git clone git@github.com:dhrhee-26/njt-submissions.git workspace
cd workspace
git checkout interns/YOUR-HANDLE
cd ..
```

**Replace `YOUR-HANDLE`** with the handle the admin gave you (e.g., `alice`).

(Cloning uses SSH because the submissions repo is private. Your SSH key from Part 3 handles the auth — no password prompt.)

If `git checkout interns/YOUR-HANDLE` says *"pathspec did not match"*, the admin hasn't created your branch yet — ask them to create `interns/YOUR-HANDLE` on `dhrhee-26/njt-submissions`.

This `workspace/` folder — checked out on **your** branch — is where everything happens from now on: your alpha code, your notebooks, and (once you submit) your results. It's a normal git repo you can `git add` / `git commit` / `git push` like any other; `submit()` just automates that from inside Jupyter.

### 4.3 Copy the starter alphas into your workspace

```bash
cp my-alphas/my_first_alpha.py my-alphas/my_first_order_book_alpha.py workspace/
```

Copies the guide's two starter alphas (one per pattern) into your workspace, so they show up in Jupyter Lab in Part 6. You can also just write a file from scratch instead — nothing depends on these being there.

### 4.4 Verify the final layout

From inside `~/njt-contest`, run:

```bash
ls
```

Expected (in some order):
```
README.md           docker-compose.yml    my-alphas    setup.md
alpha_anatomy.md    rules.md              templates    workspace
```

If all of those are there, Part 4 is done.

---

## Part 5 — Start the container (~5 minutes for the first time)

> **Before you run this**: make sure you completed **Part 3.2** (`git config --global user.name/email …`). The container mounts your host's `~/.gitconfig` so that `git` inside the container shares your identity. If that file does not exist when you run `docker compose up`, Docker silently creates `~/.gitconfig` as an **empty directory**, which then breaks `git` both on the host and in the container. If you skipped Part 3.2, do it now — otherwise see the matching row in Troubleshooting to recover.

From `~/njt-contest`:

```bash
docker compose up -d
```

**What happens:**
- The first time, Docker downloads the ~1 GB image. You'll see lines like "Pulling njt", progress bars, "Pull complete" messages. Expect ~3-5 minutes depending on your internet.
- After the pull, Docker starts the container in the background. The prompt returns when it's ready.

**Verify the container is running:**

```bash
docker compose ps
```

Expected: a line that shows `njt` with status `Up` or `running`.

```
NAME    IMAGE                                       STATUS              PORTS
njt     ghcr.io/dhrhee-26/njt-dash:main         Up 30 seconds       0.0.0.0:8050->8050/tcp, 0.0.0.0:8888->8888/tcp
```

If `STATUS` says `Exited` or `Restarting`, something went wrong. See Troubleshooting.

**Open the two web interfaces:**

In your browser, open these two URLs in **separate tabs**:

- http://localhost:8888 — **Jupyter Lab** (where you write alphas)
- http://localhost:8050 — **dash UI** (where results are compared)

Both pages should load within ~5-10 seconds. If they show "This site can't be reached" or similar, wait another 20 seconds for the container to finish starting, then try again.

---

## Part 6 — Your first alpha (~10 minutes)

You'll do this inside the **Jupyter Lab** browser tab (http://localhost:8888).

### 6.1 Tour of Jupyter Lab

When you first open it, you'll see:
- **Left sidebar**: a file browser rooted at your `workspace/`. It shows the two starter alphas you copied in Part 4.3 — one per pattern:
  - `my_first_alpha.py` — `target_weight` pattern (continuous portfolio reweights)
  - `my_first_order_book_alpha.py` — `order_book` pattern (discrete entry/exit orders)
- **Main area**: a Launcher with tiles like "Notebook", "Terminal", "File", etc.
- **Top menu bar**: File / Edit / View / Run / Kernel / ...

### 6.2 Open the starter and skim it

Double-click `my_first_alpha.py` in the left sidebar to open it. It's a short, complete example of a target_weight alpha — fetches BTC + ETH daily close, computes a 10-day cross-sectional momentum signal, ranks and goes long/short.

The walkthrough below uses `my_first_alpha.py`, but everything works identically for `my_first_order_book_alpha.py` if you'd rather start from the event-driven pattern — open that file instead.

(Want to restart from the canonical template? From a host terminal: `cp ~/njt-contest/templates/target_weight_template.py ~/njt-contest/workspace/my_first_alpha.py` — or `templates/order_book_template.py` over `my_first_order_book_alpha.py`.)

### 6.3 Create a notebook to run it

1. Click **File → New → Notebook** in the top menu
2. When asked which kernel, pick **Python 3** (the default)
3. A blank notebook opens with one empty cell
4. **Save** it: File → Save Notebook As → type `try_it.ipynb` → Save

### 6.4 Run the example alpha

In the empty cell, paste:

```python
%load my_first_alpha.py
```

Press **Shift + Enter** (this means "run the cell"). The cell will be replaced with the entire contents of `my_first_alpha.py` (preceded by a `# %load` comment).

Press **Shift + Enter** again to run the code.

The first run downloads daily-close data for BTC and ETH from Binance Vision (~1 minute on first invocation, cached afterwards). When it finishes you should see:
1. A printed line like `SimulationResult(return=+27.82%, sharpe=+0.60, ...)`
2. A **Summary** block listing 20 metrics
3. An interactive NAV chart that you can zoom and hover on

Congratulations — you've just run your first backtest.

### 6.5 Now modify the signal

Find the line with the comment `← write your signal here` (it's inside the `Alpha.get()` method). It looks like:

```python
        # 2. Signal — your alpha logic goes here.   ←  write your signal here
        #    Below is the default: 10-day cross-sectional momentum.
        signal = close.pct_change(LOOKBACK)
```

Try changing `LOOKBACK = 10` (defined at the top of the file) to a different value like `LOOKBACK = 60`. Re-run the cell with Shift+Enter. The result should change.

This is the basic loop: edit signal → Shift+Enter → see new result → iterate.

Once you're happy with momentum and want a richer cross-section, expand `SYMBOLS` to the full 9 majors listed in `~/njt-contest/rules.md`.

---

## Part 7 — Compare with built-in alphas in dash

Open the **dash UI** tab in your browser: http://localhost:8050

You'll see:
- A **Strategies** dropdown on the upper-left
- A date range picker
- A **RUN BACKTEST** button
- Several charts placeholders

Click the Strategies dropdown. You'll see groups:
- **benchmark** — buy-hold strategies for each major + an equal-weight basket (10 strategies)
- **submission** — your own submissions, plus any peers you've pulled in with `sync_peers.sh` (Part 9) — empty until you submit your first alpha

Select one or two strategies, then click **RUN BACKTEST**. After a few seconds, NAV charts, drawdown, and a statistics table appear. Spend a few minutes exploring.

After you submit your own alpha (next part), it appears under the **submission** group in this same dropdown — no waiting on anyone.

---

## Part 8 — Submit (your first attempt) (~2 minutes)

When you have an alpha you're happy with, you submit it from one notebook cell.

In the same `try_it.ipynb` notebook (or a new cell at the bottom):

```python
from framework import submit

submit(
    Alpha(),                           # the Alpha class from the cell above
    strategy_id="my_first_alpha_v1",   # folder name on your branch (your choice)
    name="My First Alpha",             # human-readable label shown in dash
    preset="binance_um_perpetual",
    description="Trying out the contest.",
)
```

`submit()` writes `positions.parquet` + `meta.json` under `interns/YOUR-HANDLE/my_first_alpha_v1/`, then `git add -A` (your **whole** workspace — the alpha file too, not just the results folder), commits, and pushes straight to the branch you're on (it must be `interns/YOUR-HANDLE` — that's what you checked out in Part 4.2).

Press Shift+Enter. After a few seconds, you should see something like:

```
✓ submitted: interns/YOUR-HANDLE/my_first_alpha_v1
  commit:    abc1234567  on interns/YOUR-HANDLE (pushed)
```

That's it — nothing else to do. No PR, nobody to wait on for merge. Refresh http://localhost:8050 and your alpha is already in the **submission** group.

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

This checks out each peer's full branch under `workspace/peers/<peer>/` (their code — agent, notebooks, everything) and regenerates `universe.json`. Refresh http://localhost:8050 — their alphas now show up in the **submission** group too. Open `peers/<peer>/` in Jupyter Lab's file browser to read their actual code. Re-run the script any time to pick up new pushes.

---

## Part 10 — Daily routine

Once setup is done, your daily workflow is just:

```bash
# Start of day
cd ~/njt-contest
docker compose up -d
# Open browser at http://localhost:8888 and http://localhost:8050

# Iterate on your alpha in Jupyter Lab...
# Submit via a cell when ready (Part 8 pattern)...

# See peers' latest work (optional, any time)
cd workspace && ./tools/sync_peers.sh && cd ..

# End of day
docker compose down
```

That's it.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| **Terminal**: `command not found: docker` | Docker Desktop isn't installed or not in PATH | Reinstall Docker Desktop; on Mac, sometimes you need to log out and back in |
| `Cannot connect to the Docker daemon` | Docker Desktop isn't running | Open Docker Desktop, wait for the whale icon to stop animating, then retry |
| Host `git` says `fatal: ... ~/.gitconfig: Is a directory`, or container says `unable to auto-detect email address` even though you set `user.email` | You ran `docker compose up` before Part 3.2, so Docker created `~/.gitconfig` as an empty folder instead of a file | `docker compose down`, then `rm -rf ~/.gitconfig`, then redo **Part 3.2** (`git config --global user.name/email …`), then `docker compose up -d`. Verify with `test -f ~/.gitconfig && echo ok` |
| `docker compose up` says "port already in use" (8888 or 8050) | Another program is using that port | Run `docker compose down`. Find the offender: Mac/Linux `lsof -i :8888`, Windows `netstat -ano \| findstr 8888`. Stop that program. Try `up -d` again |
| Browser at http://localhost:8888 says "This site can't be reached" | Container failed to start, or browser cached old result | Run `docker compose ps` — if STATUS isn't "Up", run `docker compose logs njt` to see why. If status is Up, wait 20 seconds, hard-refresh browser (Cmd+Shift+R) |
| `submit()` says `you're on branch 'main', not interns/<handle>` | You cloned `njt-submissions` but didn't check out your branch (Part 4.2) | `cd ~/njt-contest/workspace && git checkout interns/YOUR-HANDLE`, then `docker compose down && docker compose up -d` |
| `git checkout interns/YOUR-HANDLE` says `pathspec did not match` | The admin hasn't created your branch yet | Ask the admin to create `interns/YOUR-HANDLE` on `dhrhee-26/njt-submissions` |
| `git clone git@github.com:...` says `Permission denied (publickey)` | SSH key isn't registered with GitHub | Revisit **Part 3.4** — make sure the contents of `~/.ssh/id_ed25519.pub` are pasted at https://github.com/settings/keys. Then `ssh -T git@github.com` should print "Hi `<your-username>`!" |
| Container log: `ERROR — no SSH private key found under ~/.ssh/` | The host has no SSH key, so the container has nothing to push with | Run **Part 3.3** + **3.4** on the host, then `docker compose down && docker compose up -d` |
| `submit()` says `not a git repository` | Container was started outside `~/njt-contest`, or `workspace/` wasn't cloned (mount path wrong) | `docker compose down`, confirm `~/njt-contest/workspace/.git` exists, `cd ~/njt-contest`, `docker compose up -d` |
| `tools/sync_peers.sh` shows a peer with "no commits yet" | That intern hasn't submitted anything yet | Nothing to fix — re-run the script later |
| `Alpha is not defined` in the submission cell | You ran the submission cell without first running the cell that defines `Alpha` | Run the alpha definition cell first, then the submission cell |
| Docker image download is very slow | Slow network, or peak hours | Be patient on the first pull. Subsequent updates are much smaller |
| `docker compose pull` says "denied: pulling from public registry forbidden" | Some corporate networks block GHCR | Try from a different network, or ask the admin |

If you hit anything not in the table, post in **#njt-contest** or message the admin with:
1. What you were doing (which command / cell)
2. The full error message (copy-paste it, don't paraphrase)
3. The output of `docker compose ps` and `docker compose logs njt --tail 30`

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
