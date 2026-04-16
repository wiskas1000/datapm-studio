"""Tests for the close-out gap analysis service."""

from __future__ import annotations

from data_project_manager.db.repositories.data_file import (
    AggregationLevelRepository,
    DataFileAggregationRepository,
    DataFileEntityTypeRepository,
    DataFileRepository,
    EntityTypeRepository,
)
from data_project_manager.db.repositories.deliverable import DeliverableRepository
from data_project_manager.db.repositories.person import (
    PersonRepository,
    ProjectPersonRepository,
)
from data_project_manager.db.repositories.project import ProjectRepository
from data_project_manager.db.repositories.question import RequestQuestionRepository

from datapm_studio.services.closeout import Gap, analyze_gaps


def _create_project(conn, **overrides):
    """Create a minimal project and return it."""
    defaults = {
        "title": "Test Project",
        "slug": "test-project",
        "status": "active",
    }
    defaults.update(overrides)
    repo = ProjectRepository(conn)
    return repo.create(**defaults)


def _gap_descriptions(gaps: list[Gap]) -> list[str]:
    """Extract descriptions for easier assertions."""
    return [g.description for g in gaps]


class TestAnalyzeGaps:
    """Tests for analyze_gaps()."""

    def test_empty_project_has_critical_gaps(self, db_conn):
        """A brand-new project with no metadata should flag all gaps."""
        project = _create_project(db_conn)
        gaps = analyze_gaps(project, db_conn)

        descs = _gap_descriptions(gaps)
        assert "No requestor linked to this project." in descs
        assert "No deliverables registered." in descs
        assert "No data files registered." in descs
        assert "Realized start date not set." in descs
        assert "Realized end date not set." in descs
        assert "No description set." in descs
        assert "Project status is still 'active'." in descs

    def test_no_description_gap(self, db_conn):
        """Missing description is flagged as warning."""
        project = _create_project(db_conn, description=None)
        gaps = analyze_gaps(project, db_conn)

        desc_gaps = [g for g in gaps if g.description == "No description set."]
        assert len(desc_gaps) == 1
        assert desc_gaps[0].severity == "warning"

    def test_description_set_no_gap(self, db_conn):
        """Setting a description clears that gap."""
        project = _create_project(db_conn, description="A real description")
        gaps = analyze_gaps(project, db_conn)

        descs = _gap_descriptions(gaps)
        assert "No description set." not in descs

    def test_requestor_gap(self, db_conn):
        """No requestor linked is a critical gap."""
        project = _create_project(db_conn)
        gaps = analyze_gaps(project, db_conn)

        req_gaps = [g for g in gaps if "requestor" in g.description.lower()]
        assert len(req_gaps) == 1
        assert req_gaps[0].severity == "critical"

    def test_requestor_linked_no_gap(self, db_conn):
        """Linking a requestor clears that gap."""
        project = _create_project(db_conn)
        person = PersonRepository(db_conn).create(first_name="Alice", last_name="Smith")
        ProjectPersonRepository(db_conn).add(
            project_id=project.id, person_id=person.id, role="requestor"
        )

        gaps = analyze_gaps(project, db_conn)
        descs = _gap_descriptions(gaps)
        assert "No requestor linked to this project." not in descs

    def test_non_requestor_role_still_gaps(self, db_conn):
        """A person with role 'analyst' doesn't satisfy requestor check."""
        project = _create_project(db_conn)
        person = PersonRepository(db_conn).create(first_name="Bob", last_name="Jones")
        ProjectPersonRepository(db_conn).add(
            project_id=project.id, person_id=person.id, role="analyst"
        )

        gaps = analyze_gaps(project, db_conn)
        descs = _gap_descriptions(gaps)
        assert "No requestor linked to this project." in descs

    def test_realized_dates_gap(self, db_conn):
        """Missing realized dates are flagged."""
        project = _create_project(db_conn)
        gaps = analyze_gaps(project, db_conn)

        descs = _gap_descriptions(gaps)
        assert "Realized start date not set." in descs
        assert "Realized end date not set." in descs

    def test_realized_dates_set_no_gap(self, db_conn):
        """Setting realized dates clears those gaps."""
        project = _create_project(
            db_conn, realized_start="2026-01-01", realized_end="2026-03-01"
        )
        gaps = analyze_gaps(project, db_conn)

        descs = _gap_descriptions(gaps)
        assert "Realized start date not set." not in descs
        assert "Realized end date not set." not in descs

    def test_no_deliverables_gap(self, db_conn):
        """No deliverables is a critical gap."""
        project = _create_project(db_conn)
        gaps = analyze_gaps(project, db_conn)

        del_gaps = [g for g in gaps if "No deliverables" in g.description]
        assert len(del_gaps) == 1
        assert del_gaps[0].severity == "critical"

    def test_deliverables_present_no_gap(self, db_conn):
        """Having deliverables clears that gap."""
        project = _create_project(db_conn)
        DeliverableRepository(db_conn).create(
            project_id=project.id,
            type="report",
            delivered_at="2026-03-01",
        )

        gaps = analyze_gaps(project, db_conn)
        descs = _gap_descriptions(gaps)
        assert "No deliverables registered." not in descs

    def test_undelivered_deliverables_gap(self, db_conn):
        """Deliverables without delivered_at are flagged."""
        project = _create_project(db_conn)
        DeliverableRepository(db_conn).create(
            project_id=project.id,
            type="report",
        )

        gaps = analyze_gaps(project, db_conn)
        del_gaps = [g for g in gaps if "not yet marked as delivered" in g.description]
        assert len(del_gaps) == 1
        assert del_gaps[0].severity == "critical"

    def test_all_delivered_no_gap(self, db_conn):
        """Delivered deliverables don't trigger the undelivered gap."""
        project = _create_project(db_conn)
        DeliverableRepository(db_conn).create(
            project_id=project.id,
            type="report",
            delivered_at="2026-03-01",
        )

        gaps = analyze_gaps(project, db_conn)
        descs = _gap_descriptions(gaps)
        assert not any("not yet marked as delivered" in d for d in descs)

    def test_no_data_files_gap(self, db_conn):
        """No data files is a warning gap."""
        project = _create_project(db_conn)
        gaps = analyze_gaps(project, db_conn)

        file_gaps = [g for g in gaps if "No data files" in g.description]
        assert len(file_gaps) == 1
        assert file_gaps[0].severity == "warning"

    def test_data_files_missing_sensitivity_gap(self, db_conn):
        """Data files without sensitivity are flagged as critical."""
        project = _create_project(db_conn)
        DataFileRepository(db_conn).create(
            project_id=project.id,
            file_path="data/raw.csv",
            sensitivity=None,
        )

        gaps = analyze_gaps(project, db_conn)
        sens_gaps = [g for g in gaps if "sensitivity" in g.description.lower()]
        assert len(sens_gaps) == 1
        assert sens_gaps[0].severity == "critical"

    def test_data_files_with_sensitivity_no_gap(self, db_conn):
        """Data files with sensitivity set don't trigger the gap."""
        project = _create_project(db_conn)
        DataFileRepository(db_conn).create(
            project_id=project.id,
            file_path="data/raw.csv",
            sensitivity="internal",
        )

        gaps = analyze_gaps(project, db_conn)
        descs = _gap_descriptions(gaps)
        assert not any("sensitivity" in d.lower() for d in descs)
        assert "No data files registered." not in descs

    def test_status_active_gap(self, db_conn):
        """Active status is flagged as a warning."""
        project = _create_project(db_conn, status="active")
        gaps = analyze_gaps(project, db_conn)

        status_gaps = [g for g in gaps if "active" in g.description]
        assert len(status_gaps) == 1
        assert status_gaps[0].severity == "warning"

    def test_status_done_no_gap(self, db_conn):
        """Done status doesn't trigger the active gap."""
        project = _create_project(db_conn, status="done")
        gaps = analyze_gaps(project, db_conn)

        descs = _gap_descriptions(gaps)
        assert not any("active" in d for d in descs)

    def test_critical_gaps_sorted_first(self, db_conn):
        """Critical gaps should appear before warning gaps."""
        project = _create_project(db_conn)
        gaps = analyze_gaps(project, db_conn)

        severities = [g.severity for g in gaps]
        critical_indices = [i for i, s in enumerate(severities) if s == "critical"]
        warning_indices = [i for i, s in enumerate(severities) if s == "warning"]

        if critical_indices and warning_indices:
            assert max(critical_indices) < min(warning_indices)

    def test_fix_urls_point_to_project(self, db_conn):
        """Gaps with fix_url should point to the project page."""
        project = _create_project(db_conn, slug="my-project")
        gaps = analyze_gaps(project, db_conn)

        for gap in gaps:
            if gap.fix_url is not None:
                assert "/projects/my-project" in gap.fix_url

    def test_no_request_questions_gap(self, db_conn):
        """No registered request questions is flagged as a warning."""
        project = _create_project(db_conn)
        gaps = analyze_gaps(project, db_conn)

        q_gaps = [g for g in gaps if "No request questions" in g.description]
        assert len(q_gaps) == 1
        assert q_gaps[0].severity == "warning"

    def test_request_questions_present_no_gap(self, db_conn):
        """At least one request question clears the gap."""
        project = _create_project(db_conn)
        RequestQuestionRepository(db_conn).create(
            project_id=project.id, question_text="What is the churn rate?"
        )
        gaps = analyze_gaps(project, db_conn)
        descs = _gap_descriptions(gaps)
        assert not any("No request questions" in d for d in descs)

    def test_files_missing_entity_types_gap(self, db_conn):
        """Data files without linked entity types are flagged as a warning."""
        project = _create_project(db_conn)
        DataFileRepository(db_conn).create(
            project_id=project.id,
            file_path="data/raw.csv",
            sensitivity="internal",
        )
        gaps = analyze_gaps(project, db_conn)

        et_gaps = [g for g in gaps if "missing entity types" in g.description]
        assert len(et_gaps) == 1
        assert et_gaps[0].severity == "warning"

    def test_files_with_entity_types_no_gap(self, db_conn):
        """Linking an entity type clears the entity-type gap for that file."""
        project = _create_project(db_conn)
        df = DataFileRepository(db_conn).create(
            project_id=project.id,
            file_path="data/raw.csv",
            sensitivity="internal",
        )
        et = EntityTypeRepository(db_conn).create(name="patient")
        DataFileEntityTypeRepository(db_conn).add(
            data_file_id=df.id, entity_type_id=et.id
        )

        gaps = analyze_gaps(project, db_conn)
        descs = _gap_descriptions(gaps)
        assert not any("missing entity types" in d for d in descs)

    def test_files_missing_agg_levels_gap(self, db_conn):
        """Data files without linked aggregation levels are flagged as a warning."""
        project = _create_project(db_conn)
        DataFileRepository(db_conn).create(
            project_id=project.id,
            file_path="data/raw.csv",
            sensitivity="internal",
        )
        gaps = analyze_gaps(project, db_conn)

        agg_gaps = [g for g in gaps if "missing aggregation levels" in g.description]
        assert len(agg_gaps) == 1
        assert agg_gaps[0].severity == "warning"

    def test_files_with_agg_levels_no_gap(self, db_conn):
        """Linking an aggregation level clears the agg gap for that file."""
        project = _create_project(db_conn)
        df = DataFileRepository(db_conn).create(
            project_id=project.id,
            file_path="data/raw.csv",
            sensitivity="internal",
        )
        agg = AggregationLevelRepository(db_conn).create(name="biweekly")
        DataFileAggregationRepository(db_conn).add(
            data_file_id=df.id, agg_level_id=agg.id
        )

        gaps = analyze_gaps(project, db_conn)
        descs = _gap_descriptions(gaps)
        assert not any("missing aggregation levels" in d for d in descs)
