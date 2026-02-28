# Claude Code — ImplPilot Working Guide
> Version 1.1 — reflects best practices for building with Claude Code across multiple sessions.

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
1. Decide what you're building next (one step from the spec)
2. If the spec needs updating, update it first (here in this chat or in the file directly)
3. Open Claude Code, paste the session prompt below
4. Claude Code outputs a plan — you review and approve
5. Claude Code builds — you review output file by file
6. Commit with the structured commit message format (see below)
7. Close the session. Start fresh next time.
```

Short loops, not long sessions. One step per session. Claude Code has no memory between sessions — treat that as a feature. Each session re-reads the spec from scratch, which keeps the spec authoritative.

---

## COLD-START PROMPT (first ever session — Step 1 only)

Use this once, at the very beginning of the project.

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

WHEN DONE:
- Tell me exactly what to run to verify the step works.
- Output a structured commit message in this format:

  step-[N]: [module name] — [one-line summary]

  Decisions made:
  - [any judgment calls you made and why]
  - [any spec gaps you resolved, with the option you chose]

We are starting with Step 1. Read the spec, output your plan, then wait for my "go".

---
[PASTE THE FULL CONTENTS OF IMPLPILOT_MVP_SPEC_v1.1.md HERE]
```

---

## STANDARD SESSION PROMPT (Step 2 onwards)

Use this at the start of every subsequent session. Fill in the bracketed values.

```
We are building ImplPilot. The spec is in IMPLPILOT_MVP_SPEC_v1.1.md in this repo.
Steps 1–[X] are complete and committed. We are implementing Step [X+1].

Same rules as always:

BEFORE WRITING ANY CODE:
1. Read the spec. Review the existing code to understand what's already built.
2. List every file you will create or modify.
3. Flag any genuine gaps or conflicts the spec doesn't resolve — propose two options
   and wait for direction. Do not flag things the spec already answers.
4. State what I should run to verify this step works.
Wait for my "go" before writing code.

WHILE BUILDING:
- Full file contents for every new or significantly modified file.
- No raw SQL. TypeScript strict mode. Comment the why.
- Stop and flag anything that would affect the data model, API contract, or AI behavior
  that isn't covered in the spec.

WHEN DONE:
- Tell me what to run to verify.
- Output a commit message in this format:

  step-[N]: [module name] — [one-line summary]

  Decisions made:
  - [judgment calls made and why]
  - [spec gaps resolved and which option was chosen]
```

---

## REQUESTING A CHANGE MID-BUILD

Never describe a change only in chat. Always follow this sequence:

**Step 1 — Update the spec first** (come back to this chat and ask for a spec update, or edit the file directly)

**Step 2 — Start a new Claude Code session with this prompt:**

```
We are building ImplPilot. Before writing any code, read the current spec in
IMPLPILOT_MVP_SPEC_v1.1.md and the existing codebase.

I need to make the following change:
[describe the change clearly]

This change affects step [N] which is [complete / in progress / not yet started].

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
Steps 1–12 are complete. I want to add the [Module Name] module described in
Section 14 of the spec.

Before writing any code:
1. Identify every existing file that will need to change.
2. Identify any schema migrations needed and describe the migration.
3. Identify any API contracts that will change and whether they are breaking changes.
4. Propose a build plan with sub-steps, in the same format as the spec's Section 11.

Wait for my approval before writing code.
```

---

## WHEN CLAUDE CODE GOES OFF-SPEC

```
Stop. Re-read [Section X] of the spec.

You have drifted from the design in this way: [describe specifically what's wrong].

Do not continue. Revert the last change and propose a corrected approach that
stays within the spec. Show me the approach before writing any code.
```

---

## COMMIT MESSAGE FORMAT

Use this format after every completed step. This is your decision log — six months from now you'll read the git history to understand why things are the way they are.

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

Example:
```
step-4: tag system — parser, tag_events table, auto-action pipeline

Decisions made:
- Tag processing runs as FastAPI BackgroundTask, not blocking the note save response.
  Chose this over synchronous processing to keep note creation fast; side effects
  (escalation creation, notifications) can tolerate a short delay.
- Duplicate tag_events prevented by unique constraint on (tag_id, entity_type, entity_id)
  rather than application-level deduplication. More reliable under concurrent writes.
- Unknown hashtags are silently skipped, not errored. Spec implied this but didn't
  state it explicitly — chose permissive behavior to reduce friction for users.

Files created:
- backend/app/models/tag.py
- backend/app/services/tag_service.py
- backend/app/utils/tag_parser.py
- backend/app/routers/tags.py

Files modified:
- backend/app/models/__init__.py — added tag model imports
- backend/app/routers/notes.py — wired note create/update to tag processing pipeline
```

---

## QUICK REFERENCE: WHAT NEEDS A SPEC UPDATE FIRST?

| Change type | Update spec first? |
|---|---|
| New field on an existing model | Yes — add to Section 3 |
| New API endpoint | Yes — add to Section 9 |
| Change to health score formula | Yes — update Section 5 |
| Change to AI prompt | Yes — update Section 6 |
| New tag definition | No — add via Settings UI or seed script |
| Bug fix in existing logic | No — just fix it |
| UI layout/styling change | No — unless it changes a component's props or behavior |
| New page or major component | Yes — add to Section 8 |
| New future module | Yes — add to Section 14 |

---

*ImplPilot Working Guide v1.1*
