"""Close-out routes — project completion checklist."""

from flask import Blueprint, render_template

bp = Blueprint("closeout", __name__)


@bp.route("/projects/<slug>/closeout")
def checklist(slug):
    """Show the close-out checklist for a project.

    Computes gaps on the fly (no stored state):
    - Untracked files in project folder
    - DataFiles with no sensitivity set
    - No requestor linked
    - No deliverables recorded
    - Questions without data period
    - Status still 'active'
    """
    # TODO: fetch project, run closeout.gap_analysis(project)
    project = None
    gaps = []
    return render_template("closeout/checklist.html", project=project, gaps=gaps)
