"""Close-out gap analysis — finds missing metadata for a project."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from data_project_manager.db.repositories.data_file import (
    DataFileAggregationRepository,
    DataFileEntityTypeRepository,
    DataFileRepository,
)
from data_project_manager.db.repositories.deliverable import DeliverableRepository
from data_project_manager.db.repositories.person import ProjectPersonRepository
from data_project_manager.db.repositories.question import RequestQuestionRepository


@dataclass
class Gap:
    """A single metadata gap found during close-out analysis."""

    category: str  # e.g. "files", "people", "deliverables"
    severity: str  # "critical" or "warning"
    description: str  # human-readable explanation
    fix_url: str | None  # relative URL to fix this gap (for links)
    fix_field: str | None = None  # field name for inline fix (e.g. "description")


def analyze_gaps(project, conn: sqlite3.Connection) -> list[Gap]:
    """Compute all metadata gaps for a project.

    This runs on every request — no state is stored.
    Returns a list of Gap objects sorted by severity (critical first).

    Args:
        project: Project dataclass from ProjectRepository.
        conn: SQLite connection for repository queries.
    """
    gaps: list[Gap] = []
    slug = project.slug

    # 1. Description check
    if not project.description:
        gaps.append(
            Gap(
                category="metadata",
                severity="warning",
                description="No description set.",
                fix_url=f"/projects/{slug}",
                fix_field="description",
            )
        )

    # 2. Requestor check — at least one person with role "requestor"
    persons = ProjectPersonRepository(conn).list_for_project(project.id)
    has_requestor = any(p.role == "requestor" for p in persons)
    if not has_requestor:
        gaps.append(
            Gap(
                category="people",
                severity="critical",
                description="No requestor linked to this project.",
                fix_url=f"/projects/{slug}",
                fix_field="requestor",
            )
        )

    # 3. Missing realized dates
    if not project.realized_start:
        gaps.append(
            Gap(
                category="dates",
                severity="warning",
                description="Realized start date not set.",
                fix_url=f"/projects/{slug}",
                fix_field="realized_start",
            )
        )
    if not project.realized_end:
        gaps.append(
            Gap(
                category="dates",
                severity="warning",
                description="Realized end date not set.",
                fix_url=f"/projects/{slug}",
                fix_field="realized_end",
            )
        )

    # 4. No deliverables registered
    deliverables = DeliverableRepository(conn).list_for_project(project.id)
    if not deliverables:
        gaps.append(
            Gap(
                category="deliverables",
                severity="critical",
                description="No deliverables registered.",
                fix_url=None,
            )
        )

    # 5. Undelivered deliverables
    undelivered = [d for d in deliverables if d.delivered_at is None]
    if undelivered:
        count = len(undelivered)
        gaps.append(
            Gap(
                category="deliverables",
                severity="critical",
                description=f"{count} deliverable(s) not yet marked as delivered.",
                fix_url=None,
            )
        )

    # 6. No data files registered
    data_files = DataFileRepository(conn).list_for_project(project.id)
    if not data_files:
        gaps.append(
            Gap(
                category="files",
                severity="warning",
                description="No data files registered.",
                fix_url=None,
            )
        )

    # 7. Data files missing sensitivity
    missing_sensitivity = [f for f in data_files if f.sensitivity is None]
    if missing_sensitivity:
        count = len(missing_sensitivity)
        gaps.append(
            Gap(
                category="files",
                severity="critical",
                description=f"{count} data file(s) missing sensitivity classification.",
                fix_url=None,
            )
        )

    # 7b. Data files missing entity types / aggregation levels
    if data_files:
        et_repo = DataFileEntityTypeRepository(conn)
        agg_repo = DataFileAggregationRepository(conn)
        missing_entity_types = [
            f for f in data_files if not et_repo.list_for_file(f.id)
        ]
        missing_agg_levels = [f for f in data_files if not agg_repo.list_for_file(f.id)]
        if missing_entity_types:
            count = len(missing_entity_types)
            gaps.append(
                Gap(
                    category="files",
                    severity="warning",
                    description=f"{count} data file(s) missing entity types.",
                    fix_url=f"/projects/{slug}",
                )
            )
        if missing_agg_levels:
            count = len(missing_agg_levels)
            gaps.append(
                Gap(
                    category="files",
                    severity="warning",
                    description=f"{count} data file(s) missing aggregation levels.",
                    fix_url=f"/projects/{slug}",
                )
            )

    # 7c. No request questions registered
    questions = RequestQuestionRepository(conn).list_for_project(project.id)
    if not questions:
        gaps.append(
            Gap(
                category="metadata",
                severity="warning",
                description="No request questions registered.",
                fix_url=f"/projects/{slug}",
            )
        )

    # 8. Status still active (informational — project hasn't been closed yet)
    if project.status == "active":
        gaps.append(
            Gap(
                category="status",
                severity="warning",
                description="Project status is still 'active'.",
                fix_url=f"/projects/{slug}",
            )
        )

    return sorted(gaps, key=lambda g: (g.severity != "critical", g.category))
