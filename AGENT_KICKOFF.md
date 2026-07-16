# Agent kickoff — W6: build your automatic alpha-generation system

Phase 2's real mission starts here: `njt-agent-phase2` is your starting scaffold for an LLM
agent that writes alphas. It's not a blank repo — it ships a working, deliberately minimal
baseline. Your job between now and 7/30 is to make it good (see "This week" below for the
current schedule).

---

## Get it

```bash
git clone git@github.com:dhrhee-26/njt-agent-phase2.git
cd njt-agent-phase2
uv sync                      # njt-sdk + claude-agent-sdk
claude setup-token           # log in once with the shared Claude account (admin will share it)
```

If clone says "Repository not found," you likely have a pending invite you haven't accepted
yet — check your GitHub notifications or
https://github.com/dhrhee-26/njt-agent-phase2/invitations before pinging admin.

**Before your first run, set two env vars** (the repo predates the no-Docker switch, so its
defaults still assume a container):
```bash
export NJT_SUBMISSIONS_ROOT=/absolute/path/to/njt-contest/workspace   # your njt-submissions clone
export NJT_HANDLE=<your-handle>
```
Skip this and the run stops right away at the submit step with a message telling you to export
them — there's no longer a silent fallback to `/submissions` or the literal handle `local`.

## Try it

```bash
uv run python main.py --run-id demo --topic topics/example.json run
```

This runs the whole baseline: an `alpha-developer` sub-agent loads cached data, writes one
naive `margin_weight` alpha for the topic hypothesis, in-sample backtests it, and writes it out
as a local submission. Look at:
- `../njt-agent-phase2-results/demo/artifacts/build/am.py` — the alpha it wrote
- dash (`njt-dash --submissions workspace`, the local CLI in your venv — **not** the Phase 1
  Docker `njt` container on `:8050`) — the alpha shows up as soon as the agent writes it, since
  dash reads your local `workspace/` tree; pushing it (see "Getting it onto your branch" below)
  is only what makes your peers see it

## What's frozen, what's yours

| | |
|---|---|
| **Frozen** — don't touch | `agent/contracts/artifacts.py`. Downstream steps (and any future grading) depend on this exact shape. |
| **Yours** — this is the assignment | `agent/steps/build.py` (the prompt), `workspace/.claude/agents/` (add a research fleet), `workspace/.claude/skills/` (exploration, OOS/overfit checks, reporting methodology), new steps under `agent/steps/`. |

The baseline deliberately has no exploration, no OOS check, no multi-agent fleet — one agent,
one naive alpha, in-sample only. That's the floor. Building real research rigor on top — the
way you'd design a fleet, gate ideas, check for overfitting — is the actual deliverable.

## Getting it onto your branch

The agent's `submit` step **does not push to git** — it only writes `positions.parquet` +
`meta.json` into your `njt-submissions` workspace (same tree dash reads). To actually commit +
push it, run the SDK's `submit()` yourself (same one you use for hand-written alphas), or
`git add -A && git commit && git push` from your `workspace/` clone.

## Shared account — be considerate

Everyone uses the same Claude account under a subscription usage limit, not pay-per-call. If
you're running long agent sessions, don't all pile on at once — stagger your dev runs with your
cohort.

## Scoring — check with admin for the current plan

The design intent is: your agent gets run against a held-out topic set and period you don't see,
scored on risk-adjusted return, a verification-battery pass rate, and efficiency. **That harness
isn't built yet** — treat "build something that would hold up out-of-sample" as the goal for now,
and expect more detail on the actual grading mechanics as your workflow progresses.

## Schedule

- **By 7/23** — get the baseline running end to end, then build and refine your own agent
  workflow on top of it: generate a real batch of alphas, add automatic **portfolio**
  generation, and keep a running writeup of your architecture (prompt design, verification loop,
  result management) as you iterate.
- **By 7/30** — **"Can LLM replace Quant researchers?"**: a free-form report comparing your
  Phase 1 human-designed alphas against what your agent produced, plus a **live demo of your
  final workflow**.

Questions → this channel or DM me.
