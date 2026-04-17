"""Search routes — FTS5 + metadata substring search with filters."""

from __future__ import annotations

from dataclasses import dataclass

from flask import Blueprint, current_app, render_template, request

from data_project_manager.core.search import (
    search_project_metadata,
    search_projects,
)
from data_project_manager.db.models.search import SearchResult
from data_project_manager.db.repositories.data_file import (
    AggregationLevelRepository,
    DataFileAggregationRepository,
    DataFileEntityTypeRepository,
    DataFileRepository,
    EntityTypeRepository,
)
from data_project_manager.db.repositories.person import ProjectPersonRepository
from data_project_manager.db.repositories.project import ProjectRepository
from data_project_manager.db.repositories.tag import TagRepository

bp = Blueprint("search", __name__, url_prefix="/search")

STATUS_OPTIONS = ("active", "paused", "done", "archived")


@dataclass(frozen=True)
class EnrichedResult:
    """Search result enriched with requestor + lookup metadata for display."""

    result: SearchResult
    requestor: str | None
    entity_types: list[str]
    aggregation_levels: list[str]


@dataclass(frozen=True)
class Filters:
    """Parsed filter arguments from the query string."""

    q: str
    domain: str
    status: str
    requestor: str
    date_from: str
    date_to: str
    tags: list[str]
    entity_types: list[str]
    aggregation_levels: list[str]

    @property
    def any_active(self) -> bool:
        return bool(
            self.q
            or self.domain
            or self.status
            or self.requestor
            or self.date_from
            or self.date_to
            or self.tags
            or self.entity_types
            or self.aggregation_levels
        )


def _parse_filters() -> Filters:
    def _clean_list(values: list[str]) -> list[str]:
        return [v.strip() for v in values if v.strip()]

    return Filters(
        q=request.args.get("q", "").strip(),
        domain=request.args.get("domain", "").strip(),
        status=request.args.get("status", "").strip(),
        requestor=request.args.get("requestor", "").strip(),
        date_from=request.args.get("date_from", "").strip(),
        date_to=request.args.get("date_to", "").strip(),
        tags=_clean_list(request.args.getlist("tags")),
        entity_types=_clean_list(request.args.getlist("entity_types")),
        aggregation_levels=_clean_list(request.args.getlist("aggregation_levels")),
    )


def _filter_kwargs(f: Filters) -> dict:
    return {
        "domain": f.domain or None,
        "status": f.status or None,
        "requestor": f.requestor or None,
        "date_from": f.date_from or None,
        "date_to": f.date_to or None,
        "tags": f.tags or None,
        "entity_types": f.entity_types or None,
        "aggregation_levels": f.aggregation_levels or None,
    }


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
    """Search projects via FTS5 plus metadata substring search.

    Free-text ``q`` runs an FTS5 relevance search against title,
    description, slug, and domain, and a Tier 1 substring search over
    tags, people, entity types, aggregation levels, request questions,
    and deliverable paths.  Filter kwargs (``status``, ``tags``,
    ``entity_types``, ``aggregation_levels``, ``requestor``, ``domain``,
    ``date_from``, ``date_to``) narrow both result sets uniformly.
    Metadata matches not already in the FTS5 set are appended after.
    """
    f = _parse_filters()
    conn = current_app.get_db()  # type: ignore[attr-defined]
    db_path = current_app.config.get("DATAPM_DB_PATH")

    if f.any_active:
        kwargs = _filter_kwargs(f)
        fts_results = search_projects(f.q or None, db_path=db_path, **kwargs)
        meta_results = search_project_metadata(
            f.q or None,
            db_path=db_path,
            exclude_ids=[r.id for r in fts_results],
            **kwargs,
        )
        results = fts_results + meta_results
    else:
        projects = ProjectRepository(conn).list()
        results = [
            SearchResult(
                id=p.id,
                slug=p.slug,
                title=p.title,
                description=p.description,
                status=p.status,
                domain=p.domain,
                rank=0.0,
                created_at=p.created_at,
            )
            for p in projects
        ]

    tag_options = [t.name for t in TagRepository(conn).list()]
    entity_type_options = [e.name for e in EntityTypeRepository(conn).list()]
    agg_level_options = [a.name for a in AggregationLevelRepository(conn).list()]

    return render_template(
        "search/results.html",
        results=_enrich(results),
        filters=f,
        query=f.q,
        status_options=STATUS_OPTIONS,
        tag_options=tag_options,
        entity_type_options=entity_type_options,
        agg_level_options=agg_level_options,
    )
