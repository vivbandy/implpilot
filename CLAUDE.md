# ImplPilot — Claude Code Instructions

## What this project is
An in-house project management and reporting tool for implementation teams.
Full spec: `IMPLPILOT_MVP_SPEC_v1.2.md`
Working guide and session prompts: `CLAUDE_CODE_WORKING_GUIDE_v1.2.md`

## Read these first, every session
1. Read `CLAUDE_CODE_WORKING_GUIDE_v1.2.md` — this governs how you work
2. Read `IMPLPILOT_MVP_SPEC_v1.2.md` — this is the source of truth for what to build

## Non-negotiable rules (summary — full detail in working guide)
- Output a plan and wait for "go" before writing any code
- Show full file contents for every new or significantly modified file
- No raw SQL. TypeScript strict mode. No `any`.
- Stop and flag anything that affects the data model, API contract, or AI behavior
  that isn't covered in the spec
- When done with a step, output the structured commit message format

## End of every step — required checklist
Before you consider a step complete, you must:
1. Tell me what to run to verify it works
2. Output the structured commit message (format in working guide)
3. Update the "Current build status" section of this CLAUDE.md file
   with the step just completed and the next step to build
```

Then Claude Code updates `CLAUDE.md` itself as the last action of every session. You just review it as part of your normal file review, commit it along with everything else, and the next session picks up from the right place automatically.

So the full end-of-session rhythm becomes:
```
Claude Code finishes Step N
  → outputs verify command
  → outputs commit message
  → updates CLAUDE.md

You:
  → run the verify command
  → git add . && git commit -m "[paste commit message]"
  → close session

## Current build status
Step completed: 3 — Projects + Phases Module
Next step: Step 4 — Tag System

## Model
Use Sonnet 4.6 (default on Pro). Keep sessions scoped to one step at a time
to manage context window size and usage limits.