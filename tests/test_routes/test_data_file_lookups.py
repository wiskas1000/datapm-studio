"""Tests for entity type and aggregation level management on data files."""

from __future__ import annotations

from data_project_manager.db.repositories.data_file import (
    AggregationLevelRepository,
    DataFileAggregationRepository,
    DataFileEntityTypeRepository,
    DataFileRepository,
    EntityTypeRepository,
)
from data_project_manager.db.repositories.project import ProjectRepository


def _setup(conn):
    """Create a project with one data file and return (project, data_file)."""
    project = ProjectRepository(conn).create(
        title="Test Lookups", slug="test-lookups", status="active"
    )
    data_file = DataFileRepository(conn).create(
        project_id=project.id, file_path="data/raw/test.csv"
    )
    return project, data_file


class TestEntityTypes:
    """Tests for entity type add/remove on data files."""

    def test_add_form_returns_search(self, client, db_conn):
        """GET entity type add form returns search input."""
        _, df = _setup(db_conn)
        resp = client.get(
            f"/projects/test-lookups/data-files/{df.id}/entity-types/add-form"
        )
        assert resp.status_code == 200
        assert b"Search entity types" in resp.data

    def test_search_returns_results(self, client, db_conn):
        """Search endpoint returns matching entity types."""
        _, df = _setup(db_conn)
        EntityTypeRepository(db_conn).create(name="customer")
        resp = client.get(
            f"/projects/test-lookups/data-files/{df.id}/entity-types/search?q=cust"
        )
        assert resp.status_code == 200
        assert b"customer" in resp.data

    def test_search_shows_create_option(self, client, db_conn):
        """Search with no exact match shows create option."""
        _, df = _setup(db_conn)
        resp = client.get(
            f"/projects/test-lookups/data-files/{df.id}/entity-types/search?q=newtype"
        )
        assert resp.status_code == 200
        assert b"Create" in resp.data
        assert b"newtype" in resp.data

    def test_add_entity_type(self, client, db_conn):
        """POST adds an entity type to a data file."""
        project, df = _setup(db_conn)
        et = EntityTypeRepository(db_conn).create(name="transaction")
        resp = client.post(
            f"/projects/test-lookups/data-files/{df.id}/entity-types/add",
            data={"entity_type_id": et.id},
        )
        assert resp.status_code == 200
        assert b"transaction" in resp.data

        linked = DataFileEntityTypeRepository(db_conn).list_for_file(df.id)
        assert len(linked) == 1
        assert linked[0].name == "transaction"

    def test_create_and_add_entity_type(self, client, db_conn):
        """POST create-and-add creates a new type and links it."""
        project, df = _setup(db_conn)
        resp = client.post(
            f"/projects/test-lookups/data-files/{df.id}/entity-types/create-and-add",
            data={"name": "invoice"},
        )
        assert resp.status_code == 200
        assert b"invoice" in resp.data

        linked = DataFileEntityTypeRepository(db_conn).list_for_file(df.id)
        assert len(linked) == 1
        assert linked[0].name == "invoice"

    def test_remove_entity_type(self, client, db_conn):
        """POST remove unlinks an entity type from a data file."""
        project, df = _setup(db_conn)
        et = EntityTypeRepository(db_conn).create(name="product")
        DataFileEntityTypeRepository(db_conn).add(
            data_file_id=df.id, entity_type_id=et.id
        )
        resp = client.post(
            f"/projects/test-lookups/data-files/{df.id}/entity-types/remove",
            data={"entity_type_id": et.id},
        )
        assert resp.status_code == 200

        linked = DataFileEntityTypeRepository(db_conn).list_for_file(df.id)
        assert len(linked) == 0

    def test_detail_shows_entity_types(self, client, db_conn):
        """Project detail page shows entity types for each file."""
        _, df = _setup(db_conn)
        et = EntityTypeRepository(db_conn).create(name="customer")
        DataFileEntityTypeRepository(db_conn).add(
            data_file_id=df.id, entity_type_id=et.id
        )
        resp = client.get("/projects/test-lookups")
        assert b"customer" in resp.data


class TestAggregationLevels:
    """Tests for aggregation level add/remove on data files."""

    def test_add_form_returns_search(self, client, db_conn):
        """GET agg level add form returns search input."""
        _, df = _setup(db_conn)
        resp = client.get(
            f"/projects/test-lookups/data-files/{df.id}/agg-levels/add-form"
        )
        assert resp.status_code == 200
        assert b"Search aggregation levels" in resp.data

    def test_search_returns_results(self, client, db_conn):
        """Search endpoint returns matching aggregation levels."""
        _, df = _setup(db_conn)
        AggregationLevelRepository(db_conn).create(name="daily")
        resp = client.get(
            f"/projects/test-lookups/data-files/{df.id}/agg-levels/search?q=dai"
        )
        assert resp.status_code == 200
        assert b"daily" in resp.data

    def test_search_shows_create_option(self, client, db_conn):
        """Search with no exact match shows create option."""
        _, df = _setup(db_conn)
        resp = client.get(
            f"/projects/test-lookups/data-files/{df.id}/agg-levels/search?q=biweekly"
        )
        assert resp.status_code == 200
        assert b"Create" in resp.data
        assert b"biweekly" in resp.data

    def test_add_agg_level(self, client, db_conn):
        """POST adds an aggregation level to a data file."""
        project, df = _setup(db_conn)
        agg = AggregationLevelRepository(db_conn).create(name="monthly")
        resp = client.post(
            f"/projects/test-lookups/data-files/{df.id}/agg-levels/add",
            data={"agg_level_id": agg.id},
        )
        assert resp.status_code == 200
        assert b"monthly" in resp.data

        linked = DataFileAggregationRepository(db_conn).list_for_file(df.id)
        assert len(linked) == 1
        assert linked[0].name == "monthly"

    def test_create_and_add_agg_level(self, client, db_conn):
        """POST create-and-add creates a new level and links it."""
        project, df = _setup(db_conn)
        resp = client.post(
            f"/projects/test-lookups/data-files/{df.id}/agg-levels/create-and-add",
            data={"name": "quarterly"},
        )
        assert resp.status_code == 200
        assert b"quarterly" in resp.data

        linked = DataFileAggregationRepository(db_conn).list_for_file(df.id)
        assert len(linked) == 1
        assert linked[0].name == "quarterly"

    def test_remove_agg_level(self, client, db_conn):
        """POST remove unlinks an aggregation level from a data file."""
        project, df = _setup(db_conn)
        agg = AggregationLevelRepository(db_conn).create(name="yearly")
        DataFileAggregationRepository(db_conn).add(
            data_file_id=df.id, agg_level_id=agg.id
        )
        resp = client.post(
            f"/projects/test-lookups/data-files/{df.id}/agg-levels/remove",
            data={"agg_level_id": agg.id},
        )
        assert resp.status_code == 200

        linked = DataFileAggregationRepository(db_conn).list_for_file(df.id)
        assert len(linked) == 0

    def test_detail_shows_agg_levels(self, client, db_conn):
        """Project detail page shows aggregation levels for each file."""
        _, df = _setup(db_conn)
        agg = AggregationLevelRepository(db_conn).create(name="daily")
        DataFileAggregationRepository(db_conn).add(
            data_file_id=df.id, agg_level_id=agg.id
        )
        resp = client.get("/projects/test-lookups")
        assert b"daily" in resp.data
