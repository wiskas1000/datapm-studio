"""Tests for request question routes on the project detail page."""

from __future__ import annotations

from data_project_manager.db.repositories.project import ProjectRepository
from data_project_manager.db.repositories.question import RequestQuestionRepository


def _create_project(conn, **overrides):
    """Create a minimal project and return it."""
    defaults = {
        "title": "Test Questions",
        "slug": "test-questions",
        "status": "active",
    }
    defaults.update(overrides)
    return ProjectRepository(conn).create(**defaults)


class TestQuestionsSection:
    """Tests for the questions section on the project detail page."""

    def test_detail_shows_questions_section(self, client, db_conn):
        """Project detail page should include the questions section."""
        _create_project(db_conn)
        resp = client.get("/projects/test-questions")
        assert resp.status_code == 200
        assert b"Request Questions" in resp.data

    def test_detail_shows_empty_state(self, client, db_conn):
        """Empty questions section shows placeholder text."""
        _create_project(db_conn)
        resp = client.get("/projects/test-questions")
        assert b"No request questions yet" in resp.data

    def test_detail_shows_existing_questions(self, client, db_conn):
        """Questions are displayed when they exist."""
        project = _create_project(db_conn)
        RequestQuestionRepository(db_conn).create(
            project_id=project.id,
            question_text="What is the churn rate for Q1?",
        )
        resp = client.get("/projects/test-questions")
        assert b"What is the churn rate for Q1?" in resp.data

    def test_detail_shows_data_period(self, client, db_conn):
        """Questions with data periods show the period range."""
        project = _create_project(db_conn)
        RequestQuestionRepository(db_conn).create(
            project_id=project.id,
            question_text="Revenue trend?",
            data_period_from="2026-01-01",
            data_period_to="2026-03-31",
        )
        resp = client.get("/projects/test-questions")
        assert b"2026-01-01" in resp.data
        assert b"2026-03-31" in resp.data


class TestAddQuestionForm:
    """Tests for the add-question form endpoint."""

    def test_add_form_returns_form(self, client, db_conn):
        """GET add-form returns the question form partial."""
        _create_project(db_conn)
        resp = client.get("/projects/test-questions/questions/add-form")
        assert resp.status_code == 200
        assert b"question_text" in resp.data
        assert b"data_period_from" in resp.data

    def test_add_form_404_for_missing_project(self, client):
        """Should return 404 for a nonexistent project."""
        resp = client.get("/projects/nonexistent/questions/add-form")
        assert resp.status_code == 404


class TestAddQuestion:
    """Tests for POST add question."""

    def test_add_question_success(self, client, db_conn):
        """POST with valid data creates a question and returns updated section."""
        project = _create_project(db_conn)
        resp = client.post(
            "/projects/test-questions/questions/add",
            data={
                "question_text": "What is the monthly revenue trend?",
                "data_period_from": "2026-01-01",
                "data_period_to": "2026-06-30",
            },
        )
        assert resp.status_code == 200
        assert b"What is the monthly revenue trend?" in resp.data
        assert b"No request questions yet" not in resp.data

        # Verify in DB
        questions = RequestQuestionRepository(db_conn).list_for_project(project.id)
        assert len(questions) == 1
        assert questions[0].question_text == "What is the monthly revenue trend?"
        assert questions[0].data_period_from == "2026-01-01"
        assert questions[0].data_period_to == "2026-06-30"

    def test_add_question_without_dates(self, client, db_conn):
        """POST without dates creates a question with null periods."""
        project = _create_project(db_conn)
        resp = client.post(
            "/projects/test-questions/questions/add",
            data={"question_text": "Simple question"},
        )
        assert resp.status_code == 200
        assert b"Simple question" in resp.data

        questions = RequestQuestionRepository(db_conn).list_for_project(project.id)
        assert len(questions) == 1
        assert questions[0].data_period_from is None
        assert questions[0].data_period_to is None

    def test_add_question_empty_text_shows_error(self, client, db_conn):
        """POST with empty question text returns validation error."""
        _create_project(db_conn)
        resp = client.post(
            "/projects/test-questions/questions/add",
            data={"question_text": ""},
        )
        assert resp.status_code == 200
        assert b"Question text is required" in resp.data

    def test_add_question_404_for_missing_project(self, client):
        """Should return 404 for a nonexistent project."""
        resp = client.post(
            "/projects/nonexistent/questions/add",
            data={"question_text": "test"},
        )
        assert resp.status_code == 404

    def test_add_multiple_questions(self, client, db_conn):
        """Multiple questions can be added to a project."""
        project = _create_project(db_conn)
        client.post(
            "/projects/test-questions/questions/add",
            data={"question_text": "First question"},
        )
        client.post(
            "/projects/test-questions/questions/add",
            data={"question_text": "Second question"},
        )
        resp = client.get("/projects/test-questions")
        assert b"First question" in resp.data
        assert b"Second question" in resp.data

        questions = RequestQuestionRepository(db_conn).list_for_project(project.id)
        assert len(questions) == 2
