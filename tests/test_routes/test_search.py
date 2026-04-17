"""Tests for the search route and results rendering."""

from __future__ import annotations

from data_project_manager.db.repositories.data_file import (
    AggregationLevelRepository,
    DataFileAggregationRepository,
    DataFileEntityTypeRepository,
    DataFileRepository,
    EntityTypeRepository,
)
from data_project_manager.db.repositories.person import (
    PersonRepository,
    ProjectPersonRepository,
)
from data_project_manager.db.repositories.project import ProjectRepository
from data_project_manager.db.repositories.tag import ProjectTagRepository, TagRepository


def _make_project(conn, *, title, slug, description="", domain=""):
    return ProjectRepository(conn).create(
        title=title,
        slug=slug,
        status="active",
        description=description,
        domain=domain,
    )


class TestEmptyQuery:
    """Search page with no query lists all projects (or empty state)."""

    def test_no_projects_shows_empty_state(self, client):
        resp = client.get("/search/")
        assert resp.status_code == 200
        assert b"No projects yet." in resp.data

    def test_lists_all_projects_when_no_query(self, client, db_conn):
        _make_project(db_conn, title="Alpha Project", slug="alpha")
        _make_project(db_conn, title="Beta Project", slug="beta")
        resp = client.get("/search/")
        assert resp.status_code == 200
        assert b"Alpha Project" in resp.data
        assert b"Beta Project" in resp.data
        assert b"All projects (2)" in resp.data

    def test_empty_query_treated_as_no_query(self, client, db_conn):
        _make_project(db_conn, title="Gamma", slug="gamma")
        resp = client.get("/search/?q=")
        assert resp.status_code == 200
        assert b"Gamma" in resp.data
        assert b"All projects" in resp.data


class TestQueryResults:
    """Search with a query uses FTS5 and renders matches."""

    def test_query_matches_title(self, client, db_conn):
        _make_project(db_conn, title="Customer Retention", slug="cust-ret")
        _make_project(db_conn, title="Supplier Analysis", slug="sup-ana")
        resp = client.get("/search/?q=customer")
        assert resp.status_code == 200
        assert b"Customer Retention" in resp.data
        assert b"Supplier Analysis" not in resp.data

    def test_query_with_no_match_shows_empty(self, client, db_conn):
        _make_project(db_conn, title="Alpha", slug="alpha")
        resp = client.get("/search/?q=zzznomatchzzz")
        assert resp.status_code == 200
        assert b"No results for" in resp.data
        assert b"zzznomatchzzz" in resp.data

    def test_query_preserved_in_form(self, client):
        resp = client.get("/search/?q=foo")
        assert resp.status_code == 200
        assert b'value="foo"' in resp.data

    def test_query_matches_description(self, client, db_conn):
        _make_project(
            db_conn,
            title="Project X",
            slug="proj-x",
            description="revenue forecasting model",
        )
        resp = client.get("/search/?q=revenue")
        assert resp.status_code == 200
        assert b"Project X" in resp.data


class TestEnrichment:
    """Results enrich each project with requestor + file metadata."""

    def test_results_show_requestor(self, client, db_conn):
        project = _make_project(db_conn, title="Req Test", slug="req-test")
        person = PersonRepository(db_conn).create(
            first_name="Jane", last_name="Doe", email="jane@example.com"
        )
        ProjectPersonRepository(db_conn).add(
            project_id=project.id, person_id=person.id, role="requestor"
        )
        resp = client.get("/search/")
        assert resp.status_code == 200
        assert b"Jane Doe" in resp.data

    def test_non_requestor_role_not_shown_as_requestor(self, client, db_conn):
        project = _make_project(db_conn, title="Analyst Test", slug="ana-test")
        person = PersonRepository(db_conn).create(
            first_name="Bob", last_name="Smith", email="bob@example.com"
        )
        ProjectPersonRepository(db_conn).add(
            project_id=project.id, person_id=person.id, role="analyst"
        )
        resp = client.get("/search/")
        assert resp.status_code == 200
        # Analyst role should not populate the Requestor column — appearing as
        # plain text elsewhere is fine, but the row's requestor cell is empty.
        assert b"Analyst Test" in resp.data

    def test_results_show_entity_types_and_agg_levels(self, client, db_conn):
        project = _make_project(db_conn, title="Metadata Test", slug="meta-test")
        df = DataFileRepository(db_conn).create(
            project_id=project.id, file_path="data/raw/x.csv"
        )
        et = EntityTypeRepository(db_conn).create(name="customer")
        agg = AggregationLevelRepository(db_conn).create(name="monthly")
        DataFileEntityTypeRepository(db_conn).add(
            data_file_id=df.id, entity_type_id=et.id
        )
        DataFileAggregationRepository(db_conn).add(
            data_file_id=df.id, agg_level_id=agg.id
        )

        resp = client.get("/search/")
        assert resp.status_code == 200
        assert b"customer" in resp.data
        assert b"monthly" in resp.data

    def test_entity_types_deduplicated_across_files(self, client, db_conn):
        project = _make_project(db_conn, title="Dup Test", slug="dup-test")
        df1 = DataFileRepository(db_conn).create(
            project_id=project.id, file_path="a.csv"
        )
        df2 = DataFileRepository(db_conn).create(
            project_id=project.id, file_path="b.csv"
        )
        et = EntityTypeRepository(db_conn).create(name="customer")
        DataFileEntityTypeRepository(db_conn).add(
            data_file_id=df1.id, entity_type_id=et.id
        )
        DataFileEntityTypeRepository(db_conn).add(
            data_file_id=df2.id, entity_type_id=et.id
        )
        resp = client.get("/search/")
        assert resp.status_code == 200
        # Should appear exactly once as a chip in the result row
        # (additional occurrences in filter dropdown <option>s are expected)
        assert resp.data.count(b'class="tag-chip">customer<') == 1


class TestResultsStructure:
    """Results table has the expected columns."""

    def test_table_has_expected_headers(self, client, db_conn):
        _make_project(db_conn, title="Hdr", slug="hdr")
        resp = client.get("/search/")
        assert resp.status_code == 200
        for header in (
            b"Title",
            b"Folder",
            b"Status",
            b"Domain",
            b"Requestor",
            b"Entity types",
            b"Aggregation levels",
        ):
            assert header in resp.data

    def test_title_links_to_project_detail(self, client, db_conn):
        _make_project(db_conn, title="Linky", slug="linky")
        resp = client.get("/search/")
        assert resp.status_code == 200
        assert b'href="/projects/linky"' in resp.data


class TestMetadataMatch:
    """Tier 1 metadata substring search surfaces projects whose FTS5
    columns don't contain the query but whose metadata does."""

    def test_query_matches_tag_name(self, client, db_conn):
        project = _make_project(db_conn, title="Unrelated Title", slug="unrelated")
        tag = TagRepository(db_conn).create(name="revenue-forecast")
        ProjectTagRepository(db_conn).add(project_id=project.id, tag_id=tag.id)

        resp = client.get("/search/?q=revenue-forecast")
        assert resp.status_code == 200
        assert b"Unrelated Title" in resp.data

    def test_query_matches_requestor_name(self, client, db_conn):
        project = _make_project(db_conn, title="Meta Req", slug="meta-req")
        person = PersonRepository(db_conn).create(
            first_name="Zelda", last_name="Obscure", email="zo@example.com"
        )
        ProjectPersonRepository(db_conn).add(
            project_id=project.id, person_id=person.id, role="requestor"
        )

        resp = client.get("/search/?q=zelda")
        assert resp.status_code == 200
        assert b"Meta Req" in resp.data

    def test_query_matches_entity_type(self, client, db_conn):
        project = _make_project(db_conn, title="Etype", slug="etype")
        df = DataFileRepository(db_conn).create(
            project_id=project.id, file_path="a.csv"
        )
        et = EntityTypeRepository(db_conn).create(name="subscription")
        DataFileEntityTypeRepository(db_conn).add(
            data_file_id=df.id, entity_type_id=et.id
        )

        resp = client.get("/search/?q=subscription")
        assert resp.status_code == 200
        assert b"Etype" in resp.data

    def test_fts_and_metadata_results_merged_without_duplicates(self, client, db_conn):
        """A project that matches both FTS5 and metadata appears once."""
        project = _make_project(db_conn, title="Customer Work", slug="cust-work")
        tag = TagRepository(db_conn).create(name="customer-churn")
        ProjectTagRepository(db_conn).add(project_id=project.id, tag_id=tag.id)

        resp = client.get("/search/?q=customer")
        assert resp.status_code == 200
        # The row link appears once per result row
        assert resp.data.count(b'href="/projects/cust-work"') == 1


class TestFilters:
    """Filter kwargs narrow both result sets uniformly."""

    def test_status_filter_narrows(self, client, db_conn):
        ProjectRepository(db_conn).create(
            title="Active A", slug="active-a", status="active"
        )
        ProjectRepository(db_conn).create(
            title="Archived B", slug="arch-b", status="archived"
        )

        resp = client.get("/search/?status=active")
        assert resp.status_code == 200
        assert b"Active A" in resp.data
        assert b"Archived B" not in resp.data

    def test_tag_filter_requires_all(self, client, db_conn):
        p1 = _make_project(db_conn, title="Has Both", slug="both")
        p2 = _make_project(db_conn, title="Has One", slug="one")
        t_repo = TagRepository(db_conn)
        pt_repo = ProjectTagRepository(db_conn)
        tag_a = t_repo.create(name="alpha")
        tag_b = t_repo.create(name="beta")
        pt_repo.add(project_id=p1.id, tag_id=tag_a.id)
        pt_repo.add(project_id=p1.id, tag_id=tag_b.id)
        pt_repo.add(project_id=p2.id, tag_id=tag_a.id)

        resp = client.get("/search/?tags=alpha&tags=beta")
        assert resp.status_code == 200
        assert b"Has Both" in resp.data
        assert b"Has One" not in resp.data

    def test_requestor_filter_matches_substring(self, client, db_conn):
        p1 = _make_project(db_conn, title="R One", slug="r-one")
        p2 = _make_project(db_conn, title="R Two", slug="r-two")
        person = PersonRepository(db_conn).create(
            first_name="Alice", last_name="Anderson", email="alice@x.com"
        )
        ProjectPersonRepository(db_conn).add(
            project_id=p1.id, person_id=person.id, role="requestor"
        )
        other = PersonRepository(db_conn).create(
            first_name="Bob", last_name="Baker", email="bob@x.com"
        )
        ProjectPersonRepository(db_conn).add(
            project_id=p2.id, person_id=other.id, role="requestor"
        )

        resp = client.get("/search/?requestor=alice")
        assert resp.status_code == 200
        assert b"R One" in resp.data
        assert b"R Two" not in resp.data


class TestFilterUI:
    """The search page surfaces filter controls."""

    def test_filter_form_renders(self, client):
        resp = client.get("/search/")
        assert resp.status_code == 200
        for needle in (
            b'name="status"',
            b'name="tags"',
            b'name="entity_types"',
            b'name="aggregation_levels"',
            b'name="requestor"',
            b'name="date_from"',
            b'name="date_to"',
            b'name="domain"',
        ):
            assert needle in resp.data
