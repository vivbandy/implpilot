"""
Eisenhower Matrix classification service.

Deterministic classification — no AI call, instant response.
AI-assisted classification (Step 10) will override this for unclassified tasks.

Quadrant definitions:
  DO       — urgent + important   → do immediately
  SCHEDULE — not urgent + important → plan it
  DELEGATE — urgent + not important → hand it off
  ELIMINATE — not urgent + not important → drop it

How we determine urgency and importance from task data:

URGENCY (any of these = urgent):
  - due_date is today or overdue
  - due_date is within 3 days
  - status == 'blocked'
  - priority == 'critical'

IMPORTANCE (any of these = important):
  - priority in ('critical', 'high')
  - status == 'blocked'  (blocked tasks need resolution = important)

Matrix override:
  If task.matrix_override is True, the stored matrix_quadrant is respected as-is
  and not recomputed. This lets users manually pin a task to a quadrant.
"""
from datetime import date, timedelta

from app.models.task import MatrixQuadrant, Task, TaskPriority, TaskStatus


def classify_task(task: Task) -> tuple[MatrixQuadrant, str]:
    """
    Classify a single top-level task into an Eisenhower quadrant.

    Returns (quadrant, reasoning) where reasoning is a short human-readable
    explanation of why this quadrant was chosen.

    If task.matrix_override is True, returns the stored quadrant unchanged.
    """
    # Respect manual overrides — user has deliberately pinned this quadrant
    if task.matrix_override and task.matrix_quadrant is not None:
        return task.matrix_quadrant, "Manual override — quadrant pinned by user."

    today = date.today()
    urgent = _is_urgent(task, today)
    important = _is_important(task)

    if urgent and important:
        return MatrixQuadrant.DO, _reasoning(task, urgent, important)
    elif not urgent and important:
        return MatrixQuadrant.SCHEDULE, _reasoning(task, urgent, important)
    elif urgent and not important:
        return MatrixQuadrant.DELEGATE, _reasoning(task, urgent, important)
    else:
        return MatrixQuadrant.ELIMINATE, _reasoning(task, urgent, important)


def _is_urgent(task: Task, today: date) -> bool:
    """
    Urgency signals: due soon, overdue, blocked, or critical priority.
    Any one signal is enough to mark as urgent.
    """
    if task.status == TaskStatus.BLOCKED:
        return True
    if task.priority == TaskPriority.CRITICAL:
        return True
    if task.due_date is not None:
        if task.due_date <= today + timedelta(days=3):
            return True
    return False


def _is_important(task: Task) -> bool:
    """
    Importance signals: high/critical priority or blocked (needs resolution).
    """
    if task.priority in (TaskPriority.CRITICAL, TaskPriority.HIGH):
        return True
    if task.status == TaskStatus.BLOCKED:
        return True
    return False


def _reasoning(task: Task, urgent: bool, important: bool) -> str:
    """Build a short reasoning string for the classification."""
    reasons: list[str] = []

    today = date.today()
    if task.status == TaskStatus.BLOCKED:
        reasons.append("task is blocked")
    if task.priority == TaskPriority.CRITICAL:
        reasons.append("critical priority")
    elif task.priority == TaskPriority.HIGH:
        reasons.append("high priority")
    if task.due_date is not None:
        days = (task.due_date - today).days
        if days < 0:
            reasons.append(f"overdue by {abs(days)} day(s)")
        elif days <= 3:
            reasons.append(f"due in {days} day(s)")

    urgency_label = "urgent" if urgent else "not urgent"
    importance_label = "important" if important else "not important"
    reason_str = "; ".join(reasons) if reasons else "no urgency or importance signals"
    return f"Classified as {urgency_label} + {importance_label}: {reason_str}."
