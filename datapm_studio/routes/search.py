"""Search routes — full-text search across projects."""

from __future__ import annotations

from dataclasses import dataclass

from flask import Blueprint, current_app, render_template, request

from data_project_manager.core.search import search_projects
from data_project_manager.db.models.search import SearchResult
from data_project_manager.db.repositories.data_file import (
    DataFileAggregationRepository,
    DataFileEntityTypeRepository,
    DataFileRepository,
)
from data_project_manager.db.repositories.person import ProjectPersonRepository

bp = Blueprint("search", __name__, url_prefix="/search")


@dataclass(frozen=True)
class EnrichedResult:
    """Search result enriched with requestor + lookup metadata for display."""

    result: SearchResult
    requestor: str | None
    entity_types: list[str]
    aggregation_levels: list[str]


def _enrich(results: list[SearchResult]) -> list[EnrichedResult]:
    conn = current_app.get_db()  # type: ignore[attr-defined]
    person_repo = ProjectPersonRepository(conn)
    file_repo = DataFileRepository(conn)
    et_repo = DataFileEntityTypeRepository(conn)
    agg_repo = DataFileAggregationRepository(conn)

    enriched: list[EnrichedResult] = []
    for r in results:
        persons = person_repo.list_for_project(r.id)
        requestor = next(
            (
                f"{p.first_name} {p.last_name}".strip()
                for p in persons
                if p.role == "requestor"
            ),
            None,
        )

        entity_names: set[str] = set()
        agg_names: set[str] = set()
        for data_file in file_repo.list_for_project(r.id):
            for et in et_repo.list_for_file(data_file.id):
                entity_names.add(et.name)
            for agg in agg_repo.list_for_file(data_file.id):
                agg_names.add(agg.name)

        enriched.append(
            EnrichedResult(
                result=r,
                requestor=requestor,
                entity_types=sorted(entity_names),
                aggregation_levels=sorted(agg_names),
            )
        )
    return enriched


@bp.route("/")
def search():
    """Search projects using FTS5.

    Query param: q (search string)
    """
    q = request.args.get("q", "").strip()
    enriched: list[EnrichedResult] = []
    if q:
        db_path = current_app.config.get("DATAPM_DB_PATH")
        results = search_projects(q, db_path=db_path)
        enriched = _enrich(results)
    return render_template("search/results.html", results=enriched, query=q)
