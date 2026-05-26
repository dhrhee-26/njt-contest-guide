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

## Part 3 — Set up Git and GitHub authentication (~5 minutes)

You'll push your submissions through Git to GitHub. You need:
1. Git installed (usually already there on Mac/Linux; needs install on Windows)
2. Your identity configured (name + email)
3. A way to authenticate with GitHub

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

### 3.3 Install the GitHub CLI (`gh`)

The GitHub CLI lets you authenticate easily. Install it:

**Mac (with Homebrew):**
```bash
brew install gh
```

Don't have Homebrew? Install it first:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```
Then run `brew install gh`.

**Windows:**
```bash
winget install --id GitHub.cli
```
Or download from https://cli.github.com/.

**Linux:**
Follow https://github.com/cli/cli/blob/trunk/docs/install_linux.md.

### 3.4 Authenticate with GitHub

```bash
gh auth login
```

Answer the prompts:
1. **What account do you want to log into?** → **GitHub.com**
2. **What is your preferred protocol for Git operations?** → **HTTPS**
3. **Authenticate Git with your GitHub credentials?** → **Yes**
4. **How would you like to authenticate GitHub CLI?** → **Login with a web browser**

A one-time code appears in your Terminal (something like `XXXX-XXXX`). The CLI will then open your browser. Paste the code and click **Authorize**.

Back in the Terminal, you should see:
```
✓ Authentication complete.
✓ Logged in as your-github-username
```

Verify:
```bash
gh auth status
```

Should print "Logged in to github.com account ...".

---

## Part 4 — Get the contest files (~3 minutes)

### 4.1 Clone this guide repo into `~/njt-contest`

This repo contains the `docker-compose.yml`, all the documentation (including the file you're reading), and the starter templates. Cloning it gives you everything in one shot.

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
alpha_anatomy.md    rules.md              templates
```

### 4.2 Make a workspace folder for your alpha code

```bash
mkdir my-alphas
```

This is the directory Jupyter Lab will open into. You'll put your `.py` / `.ipynb` files here.

### 4.3 Clone the submissions repo

```bash
git clone https://github.com/dhrhee-26/njt-submissions.git
```

You'll see a few lines like "Cloning into 'njt-submissions'..." and then a prompt. A new folder `njt-submissions` appeared.

### 4.4 Switch to your branch

```bash
cd njt-submissions
git checkout interns/YOUR-HANDLE
cd ..
```

**Replace `YOUR-HANDLE`** with the handle the admin gave you (e.g., `interns/alice`).

If you see:
- `Switched to a new branch 'interns/YOUR-HANDLE'` → success.
- `error: pathspec ... did not match any file(s)` → the branch doesn't exist yet. Tell the admin: "Please create my branch `interns/YOUR-HANDLE` in njt-submissions."

### 4.5 Verify the final layout

From inside `~/njt-contest`, run:

```bash
ls
```

Expected (in some order):
```
README.md           docker-compose.yml    my-alphas         setup.md
alpha_anatomy.md    rules.md              njt-submissions   templates
```

If all of those are there, Part 4 is done.

---

## Part 5 — Start the container (~5 minutes for the first time)

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
njt     ghcr.io/dhrhee-26/njt-sdk-dist:latest       Up 30 seconds       0.0.0.0:8050->8050/tcp, 0.0.0.0:8888->8888/tcp
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
- **Left sidebar**: a file browser. It shows `my-alphas/` (currently empty).
- **Main area**: a Launcher with tiles like "Notebook", "Terminal", "File", etc.
- **Top menu bar**: File / Edit / View / Run / Kernel / ...

### 6.2 Copy a starter template

The cloned guide repo includes ready-to-edit templates under `~/njt-contest/templates/`. Copy one into your workspace.

**On your host terminal (NOT inside Jupyter)**:

```bash
cp ~/njt-contest/templates/target_weight_template.py ~/njt-contest/my-alphas/my_alpha.py
```

(For an event-driven alpha later, use `templates/order_book_template.py`.)

Refresh the Jupyter Lab browser tab — `my_alpha.py` now appears in the left sidebar. Double-click it to open and read through it — a short, complete example of a target_weight alpha.

### 6.3 Create a notebook to run it

1. Click **File → New → Notebook** in the top menu
2. When asked which kernel, pick **Python 3** (the default)
3. A blank notebook opens with one empty cell
4. **Save** it: File → Save Notebook As → type `try_it.ipynb` → Save

### 6.4 Run the example alpha

In the empty cell, paste:

```python
%load my_alpha.py
```

Press **Shift + Enter** (this means "run the cell"). The cell will be replaced with the entire contents of `my_alpha.py` (preceded by a `# %load` comment).

Press **Shift + Enter** again to run the code.

After ~10 seconds, you should see:
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

---

## Part 7 — Compare with built-in alphas in dash

Open the **dash UI** tab in your browser: http://localhost:8050

You'll see:
- A **Strategies** dropdown on the upper-left
- A date range picker
- A **RUN BACKTEST** button
- Several charts placeholders

Click the Strategies dropdown. You'll see groups:
- **alpha** — 11 built-in reference alphas (e.g., "60d Momentum Top-3 Long")
- **benchmark** — buy-hold strategies for each major + an equal-weight basket

Select one or two strategies, then click **RUN BACKTEST**. After a few seconds, NAV charts, drawdown, and a statistics table appear. Spend a few minutes exploring.

After you submit your own alpha (next part), it will appear under the **submission** group in this same dropdown.

---

## Part 8 — Submit (your first attempt) (~5 minutes)

When you have an alpha you're happy with, you submit it via a notebook cell.

In the same `try_it.ipynb` notebook (or a new cell at the bottom):

```python
from framework import export_submission
import subprocess

INTERN      = "YOUR-HANDLE"               # ← put your handle here, same as your branch
STRATEGY_ID = "my_first_alpha"            # ← name this folder however you want
NAME        = "My First Alpha"            # ← human-readable label
DESCRIPTION = "Trying out the contest."

# 1) Dump positions + meta to the submissions folder
folder = export_submission(
    alpha=Alpha(),               # the Alpha class from the loaded rsi_mean_reversion.py
    intern=INTERN,
    strategy_id=STRATEGY_ID,
    name=NAME,
    preset="binance_um_perpetual",
    description=DESCRIPTION,
    submissions_root="/submissions",
)
print(f"Wrote {folder}")

# 2) Git add + commit + push
rel = str(folder.relative_to("/submissions"))
subprocess.run(["git", "-C", "/submissions", "add", rel], check=True)
subprocess.run(["git", "-C", "/submissions", "commit", "-m", f"{INTERN}: add {STRATEGY_ID}"], check=True)
subprocess.run(["git", "-C", "/submissions", "push"], check=True)
print("✓ Pushed.")
```

**Important: replace `YOUR-HANDLE`** with your actual handle (e.g., `"alice"`).

Press Shift+Enter. After a few seconds, you should see:
```
Wrote /submissions/interns/YOUR-HANDLE/my_first_alpha
✓ Pushed.
```

This means your `positions.parquet` and `meta.json` are now pushed to the `interns/YOUR-HANDLE` branch on GitHub.

### Open the PR

Back in the Jupyter Lab Terminal (or your host Terminal), run:

```bash
gh pr create --repo dhrhee-26/njt-submissions \
  --base main --head interns/YOUR-HANDLE \
  --title "YOUR-HANDLE: my_first_alpha" \
  --body "First submission."
```

Or open the GitHub UI at https://github.com/dhrhee-26/njt-submissions/pulls and click **New pull request**.

The admin will review and merge it.

After merge, the next time you `git pull origin main` on the host (see daily routine below), your alpha appears in the **submission** group of the dash dropdown — alongside other interns'.

---

## Part 9 — Daily routine

Once setup is done, your daily workflow is just:

```bash
# Start of day
cd ~/njt-contest
docker compose up -d
# Open browser at http://localhost:8888 and http://localhost:8050

# Iterate on your alpha in Jupyter Lab...
# Submit via a cell when ready (Part 8 pattern)...

# Pull others' merged submissions to see in dash
cd njt-submissions
git checkout main
git pull origin main
cd ..

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
| `docker compose up` says "port already in use" (8888 or 8050) | Another program is using that port | Run `docker compose down`. Find the offender: Mac/Linux `lsof -i :8888`, Windows `netstat -ano \| findstr 8888`. Stop that program. Try `up -d` again |
| Browser at http://localhost:8888 says "This site can't be reached" | Container failed to start, or browser cached old result | Run `docker compose ps` — if STATUS isn't "Up", run `docker compose logs njt` to see why. If status is Up, wait 20 seconds, hard-refresh browser (Cmd+Shift+R) |
| `git checkout interns/your-name` says "pathspec did not match" | The admin hasn't created your branch yet | Ask the admin to create branch `interns/your-name` on `dhrhee-26/njt-submissions` |
| `git push` says `permission denied (publickey)` | SSH auth isn't set up | Use HTTPS instead — `gh auth login` configures this automatically |
| `git push` says `Authentication failed` | GitHub credentials wrong / expired | Run `gh auth login` again |
| `export_submission` says `FileNotFoundError: /submissions` | Container was started outside `~/njt-contest` (mount path wrong) | `docker compose down`, `cd ~/njt-contest`, `docker compose up -d` |
| `Alpha is not defined` in the submission cell | You ran the submission cell without first running the cell that defines `Alpha` | Run the alpha definition cell first, then the submission cell |
| Docker image download is very slow | Slow network, or peak hours | Be patient on the first pull. Subsequent updates are much smaller |
| `docker compose pull` says "denied: pulling from public registry forbidden" | Some corporate networks block GHCR | Try from a different network, or ask the admin |

If you hit anything not in the table, post in **#njt-contest** or message the admin with:
1. What you were doing (which command / cell)
2. The full error message (copy-paste it, don't paraphrase)
3. The output of `docker compose ps` and `docker compose logs njt --tail 30`

---

## What to read next

Now that everything works, the recommended reading order is:

1. [`README.md`](./README.md) — the concise quick reference
2. [`alpha_anatomy.md`](./alpha_anatomy.md) — the Alpha class contract in depth
3. [`rules.md`](./rules.md) — contest rules and pre-PR checklist
4. [`templates/target_weight_template.py`](./templates/target_weight_template.py) — starter for cross-sectional alphas
5. [`templates/order_book_template.py`](./templates/order_book_template.py) — starter for event-driven alphas

Good luck.
