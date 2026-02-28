# Claude Code — ImplPilot Working Guide
> Version 1.2 — adds git branching workflow to session structure.

---

## MENTAL MODEL: TWO MODES

Before anything else, internalize this. Working with Claude Code means consciously switching between two modes:

**Build mode** — the plan is approved, Claude Code executes. No debates, no detours.
**Decision mode** — something isn't right or isn't covered. You stop, discuss, update the spec, then re-enter build mode.

The most common mistake: letting Claude Code stay in build mode when a decision-mode conversation needs to happen. The result is Claude making judgment calls you disagree with, already woven into multiple files, with no trace of why.

The fix: always update the spec before you build. The spec is the source of truth. Changes live in the document, not in a chat.

---

## THE WORKFLOW (follow this every session)

```
1. Decide what step you're building next
2. If the spec needs updating, update it first
3. Create a new git branch for the step (see Git Workflow below)
4. Open Claude Code, paste the session prompt
5. Claude Code outputs a plan — you review and approve
6. Claude Code builds — commit frequently with wip: prefixes
7. Verify the step works (run the verify command Claude gives you)
8. Final commit with the structured commit message
9. Merge branch to main and push
10. Update CLAUDE.md build status
11. Close the session. Start fresh next time.
```

Short loops, not long sessions. One step per session. One branch per step.

---

## GIT WORKFLOW

### One-time setup (run once when you start the project)
```bash
git init
git remote add origin https://github.com/yourusername/implpilot.git
git add .
git commit -m "init: project scaffold with spec and working guide"
git push -u origin main
```

After that first `-u` push, future pushes to main are just `git push`.

### Per-step branch workflow

**Start of every step — create a branch:**
```bash
git checkout -b step-[N]-[short-name]
# Example: git checkout -b step-3-projects-phases
```

**During the step — commit frequently as Claude Code builds:**
```bash
git add .
git commit -m "wip: [what just got built]"
# Examples:
# git commit -m "wip: phase model and migration"
# git commit -m "wip: phase_service create_default_phases"
# git commit -m "wip: phases endpoints wired up"
```

Commit after every meaningful chunk — models, migrations, a service, a router. Don't wait until the whole step is done. These are your save points. If Claude Code goes wrong mid-step, you can rewind to the last clean `wip:` commit.

**If a step goes wrong — clean reset:**
```bash
git checkout main
git branch -D step-[N]-[short-name]   # delete the bad branch
git checkout -b step-[N]-[short-name]  # start fresh
```

**End of every step — final commit, merge, push:**
```bash
# Final structured commit (use the message Claude Code outputs)
git add .
git commit -m "step-[N]: [module] — [summary]

Decisions made:
- [decision and rationale]

Files created:
- [path]

Files modified:
- [path] — [what changed]"

# Merge to main
git checkout main
git merge step-[N]-[short-name]
git push

# Optional: delete the step branch now it's merged
git branch -d step-[N]-[short-name]
```

### Verify your remote at any time
```bash
git remote -v
```

### Change your remote URL if needed
```bash
git remote set-url origin https://github.com/yourusername/new-url.git
```

---

## COLD-START PROMPT (first ever session — Step 1 only)

```
You are a senior full-stack engineer helping me build an in-house project management
tool called ImplPilot. I have a complete MVP spec that defines every module, data model,
API endpoint, tech stack decision, and build sequence.

READ THE SPEC FIRST — the full contents are pasted below.

Then follow these rules for every session, including this one:

BEFORE WRITING ANY CODE:
1. List every file you will create or modify for this step.
2. Flag any gaps or conflicts the spec doesn't resolve — describe them clearly
   and propose two options. Wait for my direction before proceeding on these.
   Do not flag things the spec already answers.
3. State what I should run to verify the step works when you're done.
Output this plan and wait for me to say "go" before writing any code.

WHILE BUILDING:
- Show me the full contents of every file you create or significantly modify.
  Never show only a diff unless I ask for one.
- No raw SQL — SQLAlchemy ORM only.
- TypeScript strict mode on the frontend. No `any` types.
- Comment the *why*, not the *what* — especially on AI prompt design,
  tag auto_action logic, and the health score formula.
- If you hit a decision the spec doesn't cover, stop and flag it.
  Do not make silent judgment calls on things that affect the data model,
  API contract, or AI behavior.
- Remind me to commit after each meaningful chunk is complete
  (e.g. "models are done — good time for a wip: commit before we continue").

WHEN DONE:
- Tell me exactly what to run to verify the step works.
- Output a structured commit message in this format:

  step-[N]: [module name] — [one-line summary]

  Decisions made:
  - [any judgment calls you made and why]
  - [any spec gaps you resolved, with the option you chose]

  Files created:
  - [path]

  Files modified:
  - [path] — [what changed]

- Remind me to: git checkout main → merge → push → update CLAUDE.md

We are starting with Step 1. Read the spec, output your plan, then wait for my "go".

---
[PASTE THE FULL CONTENTS OF IMPLPILOT_MVP_SPEC_v1.2.md HERE]
```

---

## STANDARD SESSION PROMPT (Step 2 onwards)

```
We are building ImplPilot. The spec is in IMPLPILOT_MVP_SPEC_v1.2.md in this repo.
Steps 1–[X] are complete and merged to main. We are implementing Step [X+1].

Before this session I have already run:
  git checkout -b step-[X+1]-[short-name]

Same rules as always:

BEFORE WRITING ANY CODE:
1. Read the spec. Review the existing code to understand what's already built.
2. List every file you will create or modify.
3. Flag any genuine gaps or conflicts — propose two options and wait for direction.
   Do not flag things the spec already answers.
4. State what I should run to verify this step works.
Wait for my "go" before writing code.

WHILE BUILDING:
- Full file contents for every new or significantly modified file.
- No raw SQL. TypeScript strict mode. Comment the why.
- Remind me to do a wip: commit after each meaningful chunk.
- Stop and flag anything that would affect the data model, API contract,
  or AI behavior that isn't in the spec.

WHEN DONE:
- Tell me what to run to verify.
- Output the structured commit message (format below).
- Remind me to:
    git add . && git commit -m "[paste commit message]"
    git checkout main
    git merge step-[X+1]-[short-name]
    git push
    Update CLAUDE.md: "Step completed: [X+1]"

Commit message format:
  step-[N]: [module] — [one-line summary]

  Decisions made:
  - [judgment call and why]

  Files created:
  - [path]

  Files modified:
  - [path] — [what changed]
```

---

## REQUESTING A CHANGE MID-BUILD

Never describe a change only in chat. Always follow this sequence:

**Step 1 — Update the spec first**

**Step 2 — Start a new Claude Code session:**
```
We are building ImplPilot. Before writing any code, read the current spec
in IMPLPILOT_MVP_SPEC_v1.2.md and the existing codebase.

I need to make the following change: [describe the change]

This affects step [N] which is [complete / in progress / not yet started].

Before touching anything:
1. List every file that will need to change.
2. List any schema migrations required.
3. Flag any conflicts with existing completed steps.
4. Propose an implementation plan.

Wait for my approval before writing any code.
```

---

## ADDING A FUTURE MODULE (from Section 14 of the spec)

```
Steps 1–12 are complete. I want to add the [Module Name] module
described in Section 14 of the spec.

Before writing any code:
1. Identify every existing file that will need to change.
2. Identify any schema migrations needed.
3. Identify any API contracts that will change and whether they are breaking.
4. Propose a build plan with sub-steps in the same format as the spec's Section 11.

Wait for my approval before writing code.
```

---

## WHEN CLAUDE CODE GOES OFF-SPEC

```
Stop. Re-read [Section X] of the spec.

You have drifted from the design in this way: [describe specifically].

Do not continue. Revert the last change and propose a corrected approach
that stays within the spec. Show me the approach before writing any code.
```

If you're mid-branch and want to rewind to a clean point:
```bash
git log --oneline          # find the last clean wip: commit hash
git reset --hard [hash]    # rewind to that commit
```

---

## END OF EVERY STEP — REQUIRED CHECKLIST

Claude Code must complete all of these before considering a step done:

```
□ Output the verify command (what to run to confirm it works)
□ Output the structured commit message
□ Remind user to do final commit:
    git add . && git commit -m "[commit message]"
□ Remind user to merge and push:
    git checkout main
    git merge step-[N]-[short-name]
    git push
□ Update CLAUDE.md:
    Step completed: [N] — [module name]
    Next step: [N+1] — [module name]
```

Claude Code updates `CLAUDE.md` itself as the last action of the session.

---

## COMMIT MESSAGE FORMAT

```
step-[N]: [module] — [one-line summary]

Decisions made:
- [judgment call]: [why this option over alternatives]
- [spec gap]: [which option was chosen and rationale]

Files created:
- [path]

Files modified:
- [path] — [what changed]
```

**`wip:` commits during the step (informal, no strict format needed):**
```
wip: phase model and alembic migration
wip: phase_service create_default_phases
wip: phases router wired to project creation
```

---

## QUICK REFERENCE: WHAT NEEDS A SPEC UPDATE FIRST?

| Change type | Update spec first? |
|---|---|
| New field on an existing model | Yes — Section 3 |
| New API endpoint | Yes — Section 9 |
| Change to health score formula | Yes — Section 5 |
| Change to AI prompt | Yes — Section 6 |
| Design token or component pattern change | Yes — Section 10 |
| New tag definition | No — add via Settings or seed script |
| Bug fix in existing logic | No |
| UI styling tweak within existing patterns | No |
| New page or major component | Yes — Section 11 |
| New future module | Yes — Section 14 |

---

## CLAUDE.MD TEMPLATE

Keep this file in your repo root. Claude Code reads it automatically at session start.

```markdown
# ImplPilot — Claude Code Instructions

## What this project is
An in-house project management and reporting tool for implementation teams.
Full spec: IMPLPILOT_MVP_SPEC_v1.2.md
Working guide and session prompts: CLAUDE_CODE_WORKING_GUIDE_v1.2.md

## Read these first, every session
1. Read CLAUDE_CODE_WORKING_GUIDE_v1.2.md — this governs how you work
2. Read IMPLPILOT_MVP_SPEC_v1.2.md — this is the source of truth for what to build

## Non-negotiable rules (summary — full detail in working guide)
- Output a plan and wait for "go" before writing any code
- Show full file contents for every new or significantly modified file
- No raw SQL. TypeScript strict mode. No `any`.
- Use design tokens (Section 10) — never hardcode hex colors in components
- Remind me to do wip: commits after each meaningful chunk
- Stop and flag anything affecting the data model, API contract, or AI behavior
- When done: output verify command + commit message + merge/push reminder
- Update this CLAUDE.md file as the last action of every session

## Default model
Sonnet 4.6. If a step involves significant data model or AI prompt design,
flag it and I will decide whether to use a more capable model.

## Current build status
Step completed: 0 (not started)
Next step: Step 1 — Backend Foundation
Current branch: main
```

---

*ImplPilot Working Guide v1.2*