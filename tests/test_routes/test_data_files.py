"""Tests for data file routes on the project detail page."""

from __future__ import annotations

from data_project_manager.db.repositories.data_file import DataFileRepository
from data_project_manager.db.repositories.project import ProjectRepository


def _create_project(conn, **overrides):
    """Create a minimal project and return it."""
    defaults = {
        "title": "Test Data Files",
        "slug": "test-data-files",
        "status": "active",
    }
    defaults.update(overrides)
    return ProjectRepository(conn).create(**defaults)


class TestDataFilesSection:
    """Tests for the data files section on the project detail page."""

    def test_detail_shows_data_files_section(self, client, db_conn):
        """Project detail page should include the data files section."""
        _create_project(db_conn)
        resp = client.get("/projects/test-data-files")
        assert resp.status_code == 200
        assert b"Data Files" in resp.data

    def test_detail_shows_empty_state(self, client, db_conn):
        """Empty data files section shows placeholder text."""
        _create_project(db_conn)
        resp = client.get("/projects/test-data-files")
        assert b"No data files registered yet" in resp.data

    def test_detail_shows_existing_files(self, client, db_conn):
        """Registered data files are displayed."""
        project = _create_project(db_conn)
        DataFileRepository(db_conn).create(
            project_id=project.id,
            file_path="data/raw/customers.csv",
            file_format="csv",
            sensitivity="confidential",
        )
        resp = client.get("/projects/test-data-files")
        assert b"data/raw/customers.csv" in resp.data
        assert b"csv" in resp.data
        assert b"confidential" in resp.data

    def test_detail_shows_data_period(self, client, db_conn):
        """Data files with periods show the range."""
        project = _create_project(db_conn)
        DataFileRepository(db_conn).create(
            project_id=project.id,
            file_path="data/raw/sales.parquet",
            data_period_from="2026-01-01",
            data_period_to="2026-03-31",
        )
        resp = client.get("/projects/test-data-files")
        assert b"2026-01-01" in resp.data
        assert b"2026-03-31" in resp.data


class TestAddDataFileForm:
    """Tests for the add-data-file form endpoint."""

    def test_add_form_returns_form(self, client, db_conn):
        """GET add-form returns the data file registration form."""
        _create_project(db_conn)
        resp = client.get("/projects/test-data-files/data-files/add-form")
        assert resp.status_code == 200
        assert b"file_path" in resp.data
        assert b"sensitivity" in resp.data

    def test_add_form_404_for_missing_project(self, client):
        """Should return 404 for a nonexistent project."""
        resp = client.get("/projects/nonexistent/data-files/add-form")
        assert resp.status_code == 404


class TestAddDataFile:
    """Tests for POST add data file."""

    def test_add_data_file_success(self, client, db_conn):
        """POST with valid data creates a file and returns updated section."""
        project = _create_project(db_conn)
        resp = client.post(
            "/projects/test-data-files/data-files/add",
            data={
                "file_path": "data/raw/transactions.csv",
                "file_format": "csv",
                "sensitivity": "client_confidential",
                "is_source": "1",
                "data_period_from": "2026-01-01",
                "data_period_to": "2026-06-30",
                "retention_date": "2028-01-01",
            },
        )
        assert resp.status_code == 200
        assert b"data/raw/transactions.csv" in resp.data
        assert b"No data files registered yet" not in resp.data

        files = DataFileRepository(db_conn).list_for_project(project.id)
        assert len(files) == 1
        assert files[0].file_path == "data/raw/transactions.csv"
        assert files[0].file_format == "csv"
        assert files[0].sensitivity == "client_confidential"
        assert files[0].is_source is True
        assert files[0].data_period_from == "2026-01-01"
        assert files[0].retention_date == "2028-01-01"

    def test_add_data_file_minimal(self, client, db_conn):
        """POST with only file_path creates a file with defaults."""
        project = _create_project(db_conn)
        resp = client.post(
            "/projects/test-data-files/data-files/add",
            data={"file_path": "output/report.xlsx"},
        )
        assert resp.status_code == 200
        assert b"output/report.xlsx" in resp.data

        files = DataFileRepository(db_conn).list_for_project(project.id)
        assert len(files) == 1
        assert files[0].file_format is None
        assert files[0].sensitivity is None
        assert files[0].is_source is False  # checkbox unchecked

    def test_add_data_file_empty_path_shows_error(self, client, db_conn):
        """POST with empty file path returns validation error."""
        _create_project(db_conn)
        resp = client.post(
            "/projects/test-data-files/data-files/add",
            data={"file_path": ""},
        )
        assert resp.status_code == 200
        assert b"File path is required" in resp.data

    def test_add_data_file_404_for_missing_project(self, client):
        """Should return 404 for a nonexistent project."""
        resp = client.post(
            "/projects/nonexistent/data-files/add",
            data={"file_path": "test.csv"},
        )
        assert resp.status_code == 404

    def test_add_multiple_files(self, client, db_conn):
        """Multiple files can be registered to a project."""
        project = _create_project(db_conn)
        client.post(
            "/projects/test-data-files/data-files/add",
            data={"file_path": "data/file1.csv", "is_source": "1"},
        )
        client.post(
            "/projects/test-data-files/data-files/add",
            data={"file_path": "data/file2.csv", "is_source": "1"},
        )
        resp = client.get("/projects/test-data-files")
        assert b"data/file1.csv" in resp.data
        assert b"data/file2.csv" in resp.data

        files = DataFileRepository(db_conn).list_for_project(project.id)
        assert len(files) == 2
