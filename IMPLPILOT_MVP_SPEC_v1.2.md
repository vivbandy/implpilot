# ImplPilot — MVP Specification v1.2
> **For Claude Code**: This document is the complete implementation spec. Build this top-down, module by module, following the sequence in Section 11. Ask no questions — all decisions are made here. If something is ambiguous, apply the principle: *simplest working solution that doesn't close off future extensibility*.
>
> **v1.2 changes from v1.1**:
> - Section 3.3: Project Phases data model (new table, sits between projects and tasks)
> - Section 3.4: Tasks updated — `phase_id` required, `parent_task_id` added for sub-tasks
> - Section 3: Notes/Attachments/ExternalTickets entity_type enums updated to include 'phase'
> - Section 9: API endpoints updated for phases and sub-tasks
> - Section 10 (NEW): Design System — color tokens, typography, component patterns
> - Section 11: Build sequence updated (Phase module is Step 3, between Projects and Tags)

---

## 1. Project Overview

**ImplPilot** is a lightweight, in-house project management and reporting tool built for implementation teams at early-stage SaaS companies. It solves the fragmentation problem: project state living across Slack, Salesforce, Rocketlane, Google Sheets, and people's heads.

**Core design principles:**
- **Low friction first**: Every data entry flow should take seconds, not minutes.
- **Signal over manual entry**: Tags in notes and tasks automatically derive escalations, feature requests, and sentiment.
- **Structured by default**: Projects always have phases. Tasks always belong to a phase. Structure is built in, not bolted on.
- **AI-synthesized narrative**: Raw data + tag signals → readable leadership reports, automatically.
- **Modular by design**: Every feature is a self-contained module. Integrations added later without restructuring the core.
- **Does one thing exceptionally well**: Project management + reporting for implementation teams.

---

## 2. Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| **Backend** | Python 3.11+ / FastAPI | Lightweight, async, great for AI integration |
| **Database** | SQLite (dev) → Supabase PostgreSQL (prod) | Local-first, easy migration path |
| **ORM** | SQLAlchemy 2.0 (async) + Alembic | Migrations-first |
| **Frontend** | React 18 + Vite + TypeScript | Fast dev cycle, component-based |
| **UI Library** | shadcn/ui + Tailwind CSS | Clean, customizable, accessible |
| **Charts** | Recharts | Lightweight, composable |
| **State Management** | Zustand | Simple, no Redux overhead |
| **AI / Reports** | Anthropic Claude API (claude-sonnet) | Report synthesis, health scoring, NL queries |
| **Auth** | JWT (python-jose) + bcrypt | Simple, stateless, upgradeable to SSO |
| **PDF Export** | WeasyPrint | HTML-to-PDF, server-side |
| **Email** | Resend (free tier) | Simple transactional email |
| **Hosting (MVP)** | Local dev → Vercel (frontend) + Railway (backend) | Free tiers, easy CI/CD |
| **Future Hosting** | GCP Cloud Run + Cloud SQL | Drop-in container replacement |

### Directory Structure
```
implpilot/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── project.py
│   │   │   ├── phase.py              # NEW
│   │   │   ├── task.py               # updated: phase_id, parent_task_id
│   │   │   ├── tag.py
│   │   │   ├── related_objects.py
│   │   │   ├── notification.py
│   │   │   └── report.py
│   │   ├── schemas/
│   │   │   └── (mirrors models/)
│   │   ├── routers/
│   │   │   ├── auth.py
│   │   │   ├── projects.py
│   │   │   ├── phases.py             # NEW
│   │   │   ├── tasks.py
│   │   │   ├── tags.py
│   │   │   ├── related_objects.py
│   │   │   ├── reports.py
│   │   │   └── notifications.py
│   │   ├── services/
│   │   │   ├── auth_service.py
│   │   │   ├── project_service.py
│   │   │   ├── phase_service.py      # NEW
│   │   │   ├── task_service.py
│   │   │   ├── tag_service.py
│   │   │   ├── ai_service.py
│   │   │   ├── report_service.py
│   │   │   ├── matrix_service.py
│   │   │   ├── notification_service.py
│   │   │   └── external_ticket_service.py
│   │   └── utils/
│   │       ├── tag_parser.py
│   │       ├── pdf_generator.py
│   │       └── health_calculator.py
│   ├── alembic/
│   ├── tests/
│   ├── .env.example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── styles/
│   │   │   └── tokens.css            # NEW: design tokens (see Section 10)
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Projects.tsx
│   │   │   ├── ProjectDetail.tsx     # updated: phase stepper + phase tabs
│   │   │   ├── TaskDetail.tsx
│   │   │   ├── Reports.tsx
│   │   │   └── Settings.tsx
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   ├── projects/
│   │   │   ├── phases/               # NEW
│   │   │   │   ├── PhaseStepper.tsx
│   │   │   │   └── PhaseTaskList.tsx
│   │   │   ├── tasks/
│   │   │   │   ├── TaskCard.tsx
│   │   │   │   └── SubTaskList.tsx   # NEW
│   │   │   ├── matrix/
│   │   │   ├── reports/
│   │   │   └── shared/
│   │   │       ├── HealthSpectrumBar.tsx
│   │   │       └── TagChip.tsx
│   │   ├── store/
│   │   ├── api/
│   │   └── types/
│   ├── vite.config.ts
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## 3. Data Models

### 3.1 Users
```sql
users
  id            UUID PK
  email         VARCHAR UNIQUE NOT NULL
  username      VARCHAR UNIQUE NOT NULL
  password_hash VARCHAR NOT NULL
  full_name     VARCHAR
  role          ENUM('admin', 'lead', 'viewer') DEFAULT 'lead'
  is_active     BOOLEAN DEFAULT TRUE
  created_at    TIMESTAMP
  updated_at    TIMESTAMP
```

**Roles:**
- `admin` — full read/write, user management
- `lead` — read/write on own projects, read on all others
- `viewer` — read-only, can generate/download reports

---

### 3.2 Projects
```sql
projects
  id               UUID PK
  name             VARCHAR NOT NULL
  customer_name    VARCHAR NOT NULL
  description      TEXT
  status           ENUM('active', 'at_risk', 'on_hold', 'completed', 'cancelled') DEFAULT 'active'
  health_score     INTEGER (0-100, computed — drives R/Y/G spectrum display)
  current_phase    ENUM('kickoff', 'design', 'implement', 'deploy') DEFAULT 'kickoff'
  -- denormalized for fast display; updated whenever a phase is marked active
  start_date       DATE
  target_end_date  DATE
  actual_end_date  DATE
  owner_id         UUID FK → users.id
  created_by       UUID FK → users.id
  created_at       TIMESTAMP
  updated_at       TIMESTAMP
```

---

### 3.3 Phases (NEW)

```sql
phases
  id           UUID PK
  project_id   UUID FK → projects.id NOT NULL
  name         ENUM('kickoff', 'design', 'implement', 'deploy') NOT NULL
  display_name VARCHAR NOT NULL   -- e.g. "Kick-off", "Design", "Implement", "Deploy"
  order        INTEGER NOT NULL   -- 1, 2, 3, 4 — controls display sequence
  status       ENUM('pending', 'active', 'completed') DEFAULT 'pending'
  start_date   DATE
  target_end_date DATE
  completed_at TIMESTAMP NULL
  description  TEXT               -- optional notes about what this phase involves
  created_at   TIMESTAMP
  updated_at   TIMESTAMP

UNIQUE CONSTRAINT: (project_id, name)   -- one of each phase per project
```

**Phase rules:**
- All four phases are created automatically when a project is created (via `phase_service.create_default_phases(project_id)`).
- Only one phase should be `active` at a time per project. Completing a phase auto-sets the next one to `active`.
- Phases cannot be deleted — only their status and dates updated.
- `projects.current_phase` is updated whenever a phase transitions to `active`.
- Task counts, completion %, and health contribution roll up per phase for reporting.

**Seed data per new project:**
| order | name | display_name | status |
|---|---|---|---|
| 1 | kickoff | Kick-off | active |
| 2 | design | Design | pending |
| 3 | implement | Implement | pending |
| 4 | deploy | Deploy | pending |

---

### 3.4 Tasks
```sql
tasks
  id                UUID PK
  project_id        UUID FK → projects.id NOT NULL
  -- denormalized for fast querying without joining through phases
  phase_id          UUID FK → phases.id NOT NULL
  -- every task must belong to a phase; no orphan tasks
  parent_task_id    UUID FK → tasks.id NULL
  -- NULL = top-level task. Non-null = sub-task.
  -- Sub-tasks cannot have sub-tasks (enforced at service layer, not DB constraint).
  -- Sub-tasks inherit phase_id from their parent. Service enforces this on creation.
  title             VARCHAR NOT NULL
  description       TEXT
  status            ENUM('not_started', 'in_progress', 'blocked', 'completed', 'cancelled') DEFAULT 'not_started'
  priority          ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium'
  start_date        DATE
  due_date          DATE
  completed_at      TIMESTAMP
  matrix_quadrant   ENUM('do', 'schedule', 'delegate', 'eliminate') NULL
  matrix_override   BOOLEAN DEFAULT FALSE
  order             INTEGER DEFAULT 0   -- display order within a phase
  created_by        UUID FK → users.id
  created_at        TIMESTAMP
  updated_at        TIMESTAMP

task_assignees
  task_id   UUID FK → tasks.id
  user_id   UUID FK → users.id
  PRIMARY KEY (task_id, user_id)
```

**Sub-task rules (enforced in `task_service.py`):**
- A sub-task's `phase_id` must match its parent's `phase_id`. If they differ, reject with a 422 error.
- A sub-task cannot have `parent_task_id` pointing to another sub-task (max 1 level of nesting).
- Sub-tasks appear in the UI nested under their parent. They are not shown in the Eisenhower matrix — only top-level tasks appear there.
- Sub-task completion does NOT auto-complete the parent task — the parent status is managed independently.
- Sub-tasks can have their own assignees, notes, attachments, and external tickets.
- Health score computation counts sub-tasks as tasks for overdue/blocked calculations.

---

### 3.5 Notes
```sql
notes
  id           UUID PK
  entity_type  ENUM('project', 'phase', 'task', 'feature_request', 'escalation')
  entity_id    UUID NOT NULL
  content      TEXT NOT NULL
  author_id    UUID FK → users.id
  created_at   TIMESTAMP
  updated_at   TIMESTAMP
```

---

### 3.6 Attachments
```sql
attachments
  id           UUID PK
  entity_type  ENUM('project', 'phase', 'task', 'feature_request', 'escalation')
  entity_id    UUID NOT NULL
  label        VARCHAR NOT NULL
  url          TEXT NOT NULL
  created_by   UUID FK → users.id
  created_at   TIMESTAMP
```

---

### 3.7 External Tickets
```sql
external_tickets
  id              UUID PK
  entity_type     ENUM('task', 'feature_request', 'escalation')
  entity_id       UUID NOT NULL
  ticket_system   ENUM('jira', 'zendesk', 'other')
  ticket_id       VARCHAR
  url             TEXT NOT NULL
  label           VARCHAR
  status_cache    VARCHAR
  last_synced_at  TIMESTAMP
  created_at      TIMESTAMP
```

---

### 3.8 Related Objects

#### Feature Requests
```sql
feature_requests
  id              UUID PK
  project_id      UUID FK → projects.id
  phase_id        UUID FK → phases.id NULL   -- optionally scoped to a phase
  task_id         UUID FK → tasks.id NULL
  title           VARCHAR NOT NULL
  description     TEXT
  why_important   TEXT
  priority        ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium'
  status          ENUM('open', 'under_review', 'planned', 'shipped', 'declined') DEFAULT 'open'
  requested_by    VARCHAR
  source          ENUM('manual', 'tag_derived') DEFAULT 'manual'
  source_note_id  UUID FK → notes.id NULL
  created_by      UUID FK → users.id
  created_at      TIMESTAMP
  updated_at      TIMESTAMP
```

#### Escalations
```sql
escalations
  id             UUID PK
  project_id     UUID FK → projects.id
  phase_id       UUID FK → phases.id NULL
  task_id        UUID FK → tasks.id NULL
  title          VARCHAR NOT NULL
  description    TEXT
  severity       ENUM('low', 'medium', 'high', 'critical') DEFAULT 'medium'
  status         ENUM('open', 'in_progress', 'resolved', 'closed') DEFAULT 'open'
  raised_by      VARCHAR
  source         ENUM('manual', 'tag_derived') DEFAULT 'manual'
  source_note_id UUID FK → notes.id NULL
  resolved_at    TIMESTAMP
  created_by     UUID FK → users.id
  created_at     TIMESTAMP
  updated_at     TIMESTAMP
```

#### Contacts
```sql
contacts
  id           UUID PK
  project_id   UUID FK → projects.id
  name         VARCHAR NOT NULL
  email        VARCHAR
  role         VARCHAR
  company      VARCHAR
  is_primary   BOOLEAN DEFAULT FALSE
  created_at   TIMESTAMP
```

---

### 3.9 Health Reports
```sql
health_reports
  id               UUID PK
  project_id       UUID FK → projects.id NULL
  report_type      ENUM('project_health', 'aggregate', 'nl_query') DEFAULT 'project_health'
  generated_at     TIMESTAMP
  generated_by     UUID FK → users.id
  health_score     INTEGER (0-100)
  blocks_json      JSONB
  report_data_json JSONB
  filters_json     JSONB
  is_edited        BOOLEAN DEFAULT FALSE
  created_at       TIMESTAMP
```

---

### 3.10 Notifications
```sql
notifications
  id           UUID PK
  user_id      UUID FK → users.id
  type         ENUM('task_due_soon', 'task_overdue', 'project_inactive', 'phase_completed',
                    'escalation_opened', 'tag_escalation_detected', 'mention', 'report_ready')
  title        VARCHAR
  message      TEXT
  entity_type  VARCHAR
  entity_id    UUID
  is_read      BOOLEAN DEFAULT FALSE
  sent_email   BOOLEAN DEFAULT FALSE
  created_at   TIMESTAMP
```
> Added `phase_completed` notification type — fires when a phase transitions to `completed`.

---

### 3.11 Saved Views
```sql
saved_views
  id          UUID PK
  user_id     UUID FK → users.id
  name        VARCHAR NOT NULL
  page        VARCHAR
  filters     JSONB
  created_at  TIMESTAMP
```

---

### 3.12 Tags

#### Tag Definitions
```sql
tag_definitions
  id           UUID PK
  name         VARCHAR UNIQUE NOT NULL
  category     ENUM('escalation', 'feature_request', 'sentiment', 'custom') NOT NULL
  sentiment    ENUM('negative', 'neutral', 'positive') NULL
  auto_action  ENUM('create_escalation', 'create_feature_request', 'none') DEFAULT 'none'
  description  VARCHAR
  color        VARCHAR    -- hex color for TagChip
  created_at   TIMESTAMP
```

**Built-in seed tags:**

| name | category | sentiment | auto_action |
|---|---|---|---|
| `escalated` | escalation | negative | create_escalation |
| `blockedbycustomer` | escalation | negative | create_escalation |
| `atrisk` | escalation | negative | create_escalation |
| `customerenhancement` | feature_request | neutral | create_feature_request |
| `featurerequest` | feature_request | neutral | create_feature_request |
| `productsignal` | feature_request | neutral | create_feature_request |
| `customerhappy` | sentiment | positive | none |
| `goodprogress` | sentiment | positive | none |
| `frustrated` | sentiment | negative | none |
| `churnrisk` | sentiment | negative | none |
| `slowadoption` | sentiment | negative | none |

#### Tag Events
```sql
tag_events
  id            UUID PK
  tag_id        UUID FK → tag_definitions.id
  project_id    UUID FK → projects.id
  entity_type   ENUM('note', 'task', 'external_ticket')
  entity_id     UUID NOT NULL
  author_id     UUID FK → users.id
  derived_id    UUID NULL
  created_at    TIMESTAMP
```

---

## 4. Tag System — Behavior & Rules

*(Unchanged from v1.1 — see tag_parser.py, tag_service.py, process_tags pipeline)*

**One addition**: when a tag with `auto_action='create_escalation'` or `auto_action='create_feature_request'` fires and the source entity is a task, the `phase_id` from that task is automatically copied to the created escalation or feature request.

---

## 5. Health Score & R/Y/G Spectrum

### 5.1 Health Score Computation

`health_calculator.py` computes a 0–100 score. Phase progress is now factored in.

```
score = 100
score -= min(30, (overdue_tasks / total_tasks) * 100 * 0.5)       # up to -30 overdue
score -= min(20, open_critical_escalations * 10)                   # up to -20 escalations
score -= 10 if days_since_last_note_or_task_update > 7             # -10 inactivity
score -= min(10, behind_schedule_pct * 0.2)                        # up to -10 behind trajectory
score -= min(5, blocked_tasks * 2)                                 # up to -5 blocked
score -= min(10, (negative_sentiment_tags - positive_sentiment_tags) * 2)  # sentiment
score -= min(5, tag_derived_escalations_open * 3)                  # tag escalations
score -= min(10, phases_behind_schedule * 5)                       # up to -10 if phases overdue
-- phases_behind_schedule = count of phases where target_end_date < today and status != 'completed'
score = max(0, round(score))
```

### 5.2 R/Y/G Spectrum Display

Horizontal gradient bar, no hard threshold lines.

**Color mapping:**
- 0–39: `#EF4444` → `#F97316`
- 40–69: `#F97316` → `#EAB308`
- 70–100: `#EAB308` → `#22C55E`

**Semantic labels:**
- 0–39: "At Risk"
- 40–59: "Needs Attention"
- 60–74: "On Track"
- 75–100: "Healthy"

---

## 6. AI Service Design

*(Core prompts unchanged from v1.1 — tag_summary, health report JSON schema, NL query, matrix classification all remain the same)*

**One addition to AI context**: phase progress summary is now included:

```python
context["phase_summary"] = [
  {
    "name": "Kick-off",
    "status": "completed",
    "task_total": 8,
    "task_completed": 8,
    "was_on_time": True
  },
  {
    "name": "Design",
    "status": "active",
    "task_total": 12,
    "task_completed": 7,
    "days_remaining": 4,
    "overdue_tasks": 2
  },
  ...
]
```

The AI health report prompt is updated to include:

```
...
Also assess phase-level progress. If a phase is overdue or behind,
call this out specifically in risks and next_actions.
Include a "phase_status" field in the JSON output:
"phase_status": [{ "phase": string, "assessment": "on_track" | "at_risk" | "delayed" | "completed" }]
```

---

## 7. Report System — Block-Based Editor

*(Unchanged from v1.1)*

One addition: the default health report block order now includes a `phase_progress` block:

1. `metrics` block
2. `phase_progress` block — visual stepper showing phase completion state
3. `ai_text` block — status summary + sentiment + direction
4. `tag_summary` block
5. `chart` block — task completion by phase (stacked bar)
6. `ai_text` block — risks + next actions

New block type:
```typescript
| { id: string; type: 'phase_progress'; data: PhaseProgressData; editable: false }

interface PhaseProgressData {
  phases: {
    name: string
    displayName: string
    status: 'pending' | 'active' | 'completed'
    completionPct: number
    overdueTasks: number
  }[]
}
```

---

## 8. Eisenhower Matrix Dashboard

*(Unchanged from v1.1 — only top-level tasks appear in the matrix, not sub-tasks)*

---

## 9. API Endpoints

All endpoints prefixed with `/api/v1`.

### Auth
```
POST   /auth/login
POST   /auth/logout
GET    /auth/me
```

### Projects
```
GET    /projects
POST   /projects                      → also creates 4 default phases
GET    /projects/{id}                 → includes phases array with task counts
PUT    /projects/{id}
DELETE /projects/{id}
GET    /projects/{id}/health
GET    /projects/{id}/tags
```

### Phases (NEW)
```
GET    /projects/{id}/phases                    → ordered list of phases with task summary
GET    /phases/{id}                             → phase detail with tasks
PUT    /phases/{id}                             → update dates, status, description
POST   /phases/{id}/complete                    → marks phase completed, activates next phase
GET    /phases/{id}/tasks                       → all top-level tasks for this phase
```

> No `POST` to create phases — they are always created automatically with the project.
> No `DELETE` for phases — they are permanent structure.

### Tasks
```
POST   /phases/{id}/tasks                      → create task in a phase
GET    /tasks/{id}                             → includes sub_tasks array
PUT    /tasks/{id}
DELETE /tasks/{id}
POST   /tasks/{id}/assignees
DELETE /tasks/{id}/assignees/{user_id}
POST   /tasks/{id}/subtasks                    → create sub-task under this task
GET    /tasks/{id}/subtasks                    → list sub-tasks
POST   /tasks/matrix-classify
GET    /tasks/my-matrix                        → top-level tasks only
```

> `GET /projects/{id}/tasks` still works as a convenience endpoint returning all tasks flat (for reports/export). Filtered by `parent_task_id IS NULL` by default; pass `?include_subtasks=true` to include all.

### Notes
```
POST   /notes
PUT    /notes/{id}
DELETE /notes/{id}
```

### Attachments & External Tickets
```
POST   /attachments
DELETE /attachments/{id}
POST   /external-tickets
PUT    /external-tickets/{id}
DELETE /external-tickets/{id}
```

### Tags
```
GET    /tags/definitions
POST   /tags/definitions
PUT    /tags/definitions/{id}
GET    /tags/events
```

### Related Objects
```
GET    /projects/{id}/feature-requests
POST   /projects/{id}/feature-requests
PUT    /feature-requests/{id}
DELETE /feature-requests/{id}

GET    /projects/{id}/escalations
POST   /projects/{id}/escalations
PUT    /escalations/{id}

GET    /projects/{id}/contacts
POST   /projects/{id}/contacts
PUT    /contacts/{id}
DELETE /contacts/{id}
```

### Reports
```
POST   /reports/generate/{project_id}
POST   /reports/aggregate
POST   /reports/query
GET    /reports/{id}
PUT    /reports/{id}
GET    /reports/{id}/pdf
GET    /reports/weekly-digest
```

### Notifications
```
GET    /notifications
PUT    /notifications/{id}/read
PUT    /notifications/read-all
```

### Saved Views & Users
```
GET    /saved-views
POST   /saved-views
DELETE /saved-views/{id}
GET    /users
POST   /users
PUT    /users/{id}
```

---

## 10. Design System (NEW)

### 10.1 Design Philosophy

**Reference**: Monday.com — flat, clean, low visual noise. Color as signal, not decoration.

**What this is NOT:**
- No glassmorphism, no heavy gradients (except the health spectrum bar — that's intentional signal)
- No high-contrast neon or AI-aesthetics (dark purple backgrounds, glowing elements)
- No heavy drop shadows (subtle shadows only)
- No rounded-pill everything — use a consistent small border radius

**What this IS:**
- White and light-gray surfaces
- Muted, desaturated accent colors
- Color used sparingly to indicate state (status, priority, health)
- Generous whitespace
- Clear typographic hierarchy with a single font family
- Flat cards with subtle borders, not floating cards with large shadows

---

### 10.2 Color Tokens

Define these in `frontend/src/styles/tokens.css` as CSS custom properties. Tailwind config should reference these tokens so components use `bg-surface`, `text-primary` etc. via a custom Tailwind theme extension.

```css
:root {
  /* ─── Surfaces ─────────────────────────────────── */
  --color-bg-app:        #F5F6F8;   /* page background — very light gray */
  --color-bg-surface:    #FFFFFF;   /* card / panel background */
  --color-bg-subtle:     #F0F1F3;   /* secondary surface, hover states */
  --color-bg-overlay:    #FFFFFF;   /* modals, slide-overs */

  /* ─── Borders ───────────────────────────────────── */
  --color-border:        #E4E6EA;   /* default border — subtle, not harsh */
  --color-border-strong: #C5C7D4;   /* emphasized border, active inputs */

  /* ─── Text ──────────────────────────────────────── */
  --color-text-primary:  #323338;   /* near-black, main body text */
  --color-text-secondary:#676879;   /* secondary / meta text */
  --color-text-disabled: #C5C7D4;   /* placeholder, disabled */
  --color-text-inverse:  #FFFFFF;   /* text on dark backgrounds */

  /* ─── Brand / Interactive ───────────────────────── */
  --color-brand:         #0073EA;   /* primary action color — links, buttons, focus rings */
  --color-brand-hover:   #0060C2;   /* hover state */
  --color-brand-light:   #E8F3FF;   /* brand tint for selected states, badge bg */

  /* ─── Status Colors (muted, not neon) ───────────── */
  /* Use these for status pills, priority dots, phase indicators */
  --color-status-green:  #00C875;   /* completed, healthy */
  --color-status-green-bg: #E5F9F0;
  --color-status-yellow: #FDAB3D;   /* in progress, needs attention */
  --color-status-yellow-bg: #FFF3E0;
  --color-status-red:    #E2445C;   /* blocked, at risk, overdue */
  --color-status-red-bg: #FDEEF1;
  --color-status-purple: #A25DDC;   /* not started */
  --color-status-purple-bg: #F3E9FB;
  --color-status-gray:   #C5C7D4;   /* cancelled, pending */
  --color-status-gray-bg: #F0F1F3;

  /* ─── Priority Colors ───────────────────────────── */
  --color-priority-critical: #E2445C;
  --color-priority-high:     #FDAB3D;
  --color-priority-medium:   #0073EA;
  --color-priority-low:      #C5C7D4;

  /* ─── Shadows (subtle only) ─────────────────────── */
  --shadow-card:   0 1px 4px rgba(0, 0, 0, 0.06);
  --shadow-popover: 0 4px 16px rgba(0, 0, 0, 0.10);
  --shadow-modal:  0 8px 32px rgba(0, 0, 0, 0.12);

  /* ─── Spacing scale ─────────────────────────────── */
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-5:  20px;
  --space-6:  24px;
  --space-8:  32px;
  --space-10: 40px;
  --space-12: 48px;

  /* ─── Border Radius ─────────────────────────────── */
  --radius-sm:  4px;    /* inputs, small chips */
  --radius-md:  6px;    /* cards, buttons */
  --radius-lg:  8px;    /* modals, panels */
  --radius-pill: 999px; /* status pills only */

  /* ─── Typography ─────────────────────────────────── */
  --font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-size-xs:  11px;
  --font-size-sm:  12px;
  --font-size-md:  14px;   /* base body size */
  --font-size-lg:  16px;
  --font-size-xl:  18px;
  --font-size-2xl: 22px;
  --font-size-3xl: 28px;
  --font-weight-regular: 400;
  --font-weight-medium:  500;
  --font-weight-semibold: 600;
  --font-weight-bold:    700;
  --line-height-tight:   1.3;
  --line-height-normal:  1.5;
  --line-height-relaxed: 1.7;
}
```

Install Inter: add `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap')` to `index.css`.

---

### 10.3 Tailwind Config Extension

In `tailwind.config.ts`, extend the theme to map tokens to Tailwind classes:

```typescript
theme: {
  extend: {
    colors: {
      'bg-app':       'var(--color-bg-app)',
      'bg-surface':   'var(--color-bg-surface)',
      'bg-subtle':    'var(--color-bg-subtle)',
      'border-default': 'var(--color-border)',
      'border-strong': 'var(--color-border-strong)',
      'text-primary': 'var(--color-text-primary)',
      'text-secondary': 'var(--color-text-secondary)',
      'text-disabled': 'var(--color-text-disabled)',
      'brand':        'var(--color-brand)',
      'brand-hover':  'var(--color-brand-hover)',
      'brand-light':  'var(--color-brand-light)',
      'status-green': 'var(--color-status-green)',
      'status-yellow': 'var(--color-status-yellow)',
      'status-red':   'var(--color-status-red)',
      'status-purple': 'var(--color-status-purple)',
      'status-gray':  'var(--color-status-gray)',
    },
    fontFamily: {
      sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'sans-serif'],
    },
    borderRadius: {
      sm: 'var(--radius-sm)',
      md: 'var(--radius-md)',
      lg: 'var(--radius-lg)',
      pill: 'var(--radius-pill)',
    },
    boxShadow: {
      card:    'var(--shadow-card)',
      popover: 'var(--shadow-popover)',
      modal:   'var(--shadow-modal)',
    },
  }
}
```

---

### 10.4 Component Patterns

Claude Code must use these patterns consistently. Never deviate for "visual interest."

#### Page Layout
```
AppShell:
  ├── Sidebar (240px fixed, bg-surface, right border: border-default)
  │   ├── Logo (top, 48px height)
  │   ├── Nav items (14px, text-secondary → text-primary on active, brand-light bg on active)
  │   └── User avatar + name (bottom)
  └── Main content area (bg-app, flex-1)
      ├── Page header (bg-surface, border-bottom, 56px height, px-6)
      │   ├── Page title (18px semibold, text-primary)
      │   └── Action buttons (right-aligned)
      └── Page body (px-6 py-6, max-w-screen-xl mx-auto)
```

#### Cards
```css
/* Standard card */
background: var(--color-bg-surface);
border: 1px solid var(--color-border);
border-radius: var(--radius-md);
box-shadow: var(--shadow-card);
padding: 16px;
/* NO hover lift effect. Cards are static surfaces. */
```

#### Buttons
```
Primary:   bg-brand text-white, hover:bg-brand-hover, radius-md, px-4 py-2, 14px medium
Secondary: bg-white border-default text-primary, hover:bg-bg-subtle, radius-md
Danger:    bg-status-red text-white, hover:bg-red-700
Ghost:     no bg no border, text-secondary, hover:bg-bg-subtle, hover:text-primary
Icon:      32x32px, ghost style, radius-md
```

#### Status Pills
```
/* Reusable StatusPill component */
padding: 2px 8px;
border-radius: var(--radius-pill);
font-size: 12px;
font-weight: 500;

/* Per status — background is the -bg variant, text is the color itself */
not_started: bg-status-purple-bg text-status-purple
in_progress: bg-status-yellow-bg text-status-yellow
blocked:     bg-status-red-bg text-status-red
completed:   bg-status-green-bg text-status-green
cancelled:   bg-status-gray-bg text-status-gray
```

#### Priority Dots
```
/* Small colored circle, 8px, shown next to task title */
critical: bg-priority-critical
high:     bg-priority-high
medium:   bg-priority-medium
low:      bg-priority-low
```

#### Phase Stepper (`PhaseStepper.tsx`)
```
Horizontal row of 4 steps. Each step:
  - Circle indicator (24px): empty=gray, active=brand filled, completed=status-green filled with checkmark
  - Label below (12px, text-secondary for pending, text-primary for active/completed)
  - Connector line between steps: gray for pending, brand for active→previous, green for completed

On click of a completed or active phase: navigates to that phase's task list.
Pending phases are not clickable (grayed out, cursor-default).
```

#### Task Cards
```
/* Used in phase task list and Eisenhower matrix */
bg-surface border-default radius-md shadow-card
padding: 12px 16px
layout: flex row, gap-3

Left:     priority dot (8px circle)
Center:   task title (14px medium text-primary)
          sub-info row (12px text-secondary): assignee avatars, due date, tag chips
Right:    status pill

Overdue:  left border 3px solid status-red
Blocked:  left border 3px solid status-yellow
Sub-task: 24px left indent, no shadow, lighter border (border-default opacity 60%)
```

#### Tags / Tag Chips
```
/* TagChip component */
display: inline-flex
padding: 1px 6px
border-radius: var(--radius-sm)
font-size: 11px
font-weight: 500
background: color from tag_definitions.color at 15% opacity
color: color from tag_definitions.color (full opacity)
/* Example: #escalated → red chip */
```

#### Forms & Inputs
```
Input/Textarea:
  border: 1px solid border-default
  border-radius: radius-sm
  padding: 8px 12px
  font-size: 14px
  background: bg-surface
  on focus: border-color → border-strong, outline: 2px solid brand-light

Labels: 12px semibold text-secondary, margin-bottom 4px
```

#### Empty States
```
Centered in container, text-secondary
Icon (24px, muted) above text
Primary message: 14px medium text-primary
Secondary message: 14px text-secondary
Optional CTA button below
No illustrations — keep it text + icon only
```

#### Navigation Active State
```
Active nav item:
  background: brand-light
  color: brand
  font-weight: 600
  left border: 3px solid brand
```

---

### 10.5 Page-Specific Design Notes

**Login page:**
- Centered card (480px wide) on bg-app background
- Logo above form
- No background image or gradient — just the flat gray page background
- Single card with email + password + submit

**Dashboard:**
- Project cards in a 3-column responsive grid
- Each card: customer name (12px secondary), project name (16px semibold), health spectrum bar (full width, sm size), task completion micro-bar, days remaining badge, phase indicator (current phase name)

**Project Detail:**
- `PhaseStepper` pinned below page header — always visible
- Below stepper: tab row (Tasks | Feature Requests | Escalations | Contacts | Notes | Reports)
- Task list shows tasks for the active phase by default; user can switch phase via stepper

**Task list within a phase:**
- Flat list, not kanban (kanban is too heavy for this use case)
- Sortable by due date, priority
- "Add task" row at the bottom of the list (click to expand inline form — no modal)
- Sub-tasks expand/collapse under parent with a toggle chevron

---

### 10.6 Typography Usage

```
Page titles:        22px bold   text-primary
Section headers:    16px semibold text-primary
Card titles:        14px semibold text-primary
Body / descriptions: 14px regular text-primary
Meta / timestamps:  12px regular text-secondary
Labels:             12px semibold text-secondary (uppercase for table headers)
Tag chips:          11px medium
```

---

## 11. Build Sequence (for Claude Code)

Build in this exact order. Each step must leave the app runnable.

### Step 1 — Backend Foundation
1. FastAPI scaffold, `config.py`, `database.py` (SQLite async)
2. All SQLAlchemy models including `phases`, updated `tasks` (phase_id, parent_task_id), `tag_definitions`, `tag_events`
3. Alembic init + initial migration
4. Seed script: admin user + built-in tag definitions
5. `GET /health` endpoint

### Step 2 — Auth Module
1. `auth_service.py`: user CRUD, password hashing
2. `POST /auth/login`, `GET /auth/me`
3. JWT middleware: `get_current_user` dependency

### Step 3 — Projects + Phases Module
1. Projects CRUD + filters
2. `phase_service.create_default_phases(project_id)` — called on every project creation
3. Phases endpoints: list, detail, update, complete
4. `POST /phases/{id}/complete` — marks phase complete, activates next, fires `phase_completed` notification, updates `projects.current_phase`
5. `GET /projects/{id}` returns project with phases array (task counts per phase)
6. `GET /projects/{id}/health` — deterministic score including phase penalties

### Step 4 — Tag System
1. `tag_parser.py` — `extract_tags()` with tests
2. `tag_service.py` — `process_tags()` pipeline
3. Tags endpoints
4. Notes CRUD wired to tag pipeline
5. Attachments CRUD

### Step 5 — Tasks Module
1. Tasks CRUD — `POST /phases/{id}/tasks`, enforce `phase_id` matching
2. Sub-tasks: `POST /tasks/{id}/subtasks`, enforce max 1 level depth, enforce phase_id matching parent
3. Assignees (add/remove)
4. External tickets (URL-only)
5. `matrix_service.py` — deterministic classification (top-level tasks only)
6. `GET /tasks/my-matrix` (top-level only), `POST /tasks/matrix-classify`

### Step 6 — Related Objects
1. Feature requests CRUD (with `phase_id` field)
2. Escalations CRUD (with `phase_id` field)
3. Contacts CRUD

### Step 7 — Frontend Foundation
1. Vite + React + TypeScript scaffold
2. `tokens.css` — all design tokens from Section 10.2
3. Tailwind config extension from Section 10.3
4. Install Inter font
5. shadcn/ui setup (override default colors to use token values)
6. Axios API client + JWT interceptor
7. Zustand auth store
8. Login page (centered card, flat design)
9. Protected route wrapper
10. AppShell layout (sidebar + main area per Section 10.4)
11. `StatusPill`, `PriorityDot`, `TagChip`, `HealthSpectrumBar` components

### Step 8 — Frontend Core Pages
1. Dashboard — project cards (3-col grid), My Tasks table, notification bell
2. Projects list — table view, filter bar, quick-create modal
3. Project Detail:
   - `PhaseStepper` component wired to project phases
   - Tab row
   - Task list for active phase, with sub-task expand/collapse
   - Inline "Add task" row at bottom of list
4. Task Detail slide-over — with sub-tasks section, tag chips, external tickets, notes

### Step 9 — Eisenhower Matrix
1. `EisenhowerMatrix.tsx` with `@dnd-kit/core`
2. Wire to `GET /tasks/my-matrix` (top-level tasks only)
3. Drag → `PUT /tasks/{id}` with quadrant + override
4. "My Matrix" tab on Dashboard

### Step 10 — AI & Reports Module
1. `ai_service.py` — updated prompts with phase context
2. `report_service.py` — phase_summary in context assembly
3. `health_calculator.py` — phase penalties in score
4. AI matrix classification for unclassified tasks
5. Report endpoints
6. `ReportBlockEditor.tsx` + `PhaseProgressBlock` component
7. `ChartBlock.tsx` (Recharts)
8. `AggregateReportBuilder.tsx`
9. PDF export

### Step 11 — Notifications Module
1. APScheduler daily jobs (overdue, inactive, phase deadline approaching)
2. Resend email integration
3. `NotificationDrawer` frontend component

### Step 12 — Polish
1. Saved views
2. Role-based UI gating
3. Tag management in Settings
4. Responsive layout pass
5. README

---

## 12. Environment Variables

```env
DATABASE_URL=sqlite+aiosqlite:///./implpilot.db
SECRET_KEY=<random 32-char string>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480

ANTHROPIC_API_KEY=<your key>

RESEND_API_KEY=<your key>
FROM_EMAIL=notifications@yourcompany.com

JIRA_BASE_URL=
JIRA_API_TOKEN=
ZENDESK_BASE_URL=
ZENDESK_API_TOKEN=
```

---

## 13. Out of Scope (MVP)

- Jira/Zendesk API sync
- Slack integration
- Customer-facing portal
- File uploads (S3)
- Gantt / timeline view
- Multi-tenancy
- Okta / SSO
- Mobile app
- Custom phase names (phases are always the fixed four in MVP)

---

## 14. Future Modules (Roadmap Hooks)

| Module | What it adds | Hook in place |
|---|---|---|
| Custom Phases | User-defined phase names/order | `phases` table already exists; just lift the name ENUM to VARCHAR |
| Jira Integration | Live ticket status | `external_tickets.status_cache`, service stub |
| Zendesk Integration | Pull ticket status | Same |
| Gong Transcript Ingestion | AI extracts tags/action items from transcript | `tag_service.process_tags()` + new `ai_service` method |
| Slack Bot | Notifications + `/status` | `notifications.type` enum, modular delivery |
| Customer Portal | Read-only project view | `users.role` enum, add `customer` role |
| Custom Tag Automation | Auto-escalate on tag threshold | `tag_events` queryable |
| File Uploads | Attach files to tasks | `attachments` table already polymorphic |

---

## 15. Coding Conventions

- **Backend**: Type hints everywhere. Pydantic v2 schemas. No raw SQL. Services contain logic; routers are thin.
- **Phase enforcement**: `phase_service.py` is the only place that transitions phase status. No other service should directly write `phases.status`.
- **Sub-task enforcement**: `task_service.py` enforces max depth at create time. Reject with HTTP 422 if `parent_task_id` points to a task that already has a parent.
- **Tag processing**: Always in a `BackgroundTask` — never blocks note/task write response.
- **Frontend**: TypeScript strict mode. No `any`. Components under 200 lines.
- **Design**: Use token classes (`bg-surface`, `text-primary`, etc.) everywhere. Never hardcode hex colors in components.
- **Naming**: snake_case backend, camelCase frontend, PascalCase components.
- **Error handling**: Backend returns `{ detail: string }`. Frontend shows toast on all errors.
- **Comments**: Comment the *why*, especially AI prompts, health score formula, phase transition logic.

---

*ImplPilot MVP Spec v1.2 — Ready for implementation via Claude Code.*