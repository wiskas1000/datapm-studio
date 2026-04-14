"""Close-out gap analysis — finds missing metadata for a project."""

from dataclasses import dataclass


@dataclass
class Gap:
    """A single metadata gap found during close-out analysis."""

    category: str  # e.g. "files", "people", "deliverables"
    severity: str  # "required" or "recommended"
    description: str  # human-readable explanation
    fix_url: str  # relative URL to fix this gap (for HTMX links)


def analyze_gaps(project, db_connection) -> list[Gap]:
    """Compute all metadata gaps for a project.

    This runs on every request — no state is stored.
    Returns a list of Gap objects sorted by severity.

    Args:
        project: Project dict/dataclass from ProjectRepository
        db_connection: SQLite connection for repository queries
    """
    gaps = []

    # TODO: implement each check using repository classes:
    #
    # 1. Status check — is it still "active"?
    # 2. Requestor check — is any person linked with role "requestor"?
    # 3. Deliverables check — are there any deliverables?
    # 4. DataFile sensitivity — do all registered files have sensitivity set?
    # 5. Untracked files — scan project folder, compare to DataFile table
    # 6. Questions without data period
    # 7. Missing expected_end or realized_end dates

    return sorted(gaps, key=lambda g: (g.severity != "required", g.category))
