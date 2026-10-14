"""Keep OpenSSF publication compatible and GitHub upload fail closed."""

import json
import runpy
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
REVIEWED_ACTION = "ossf/scorecard-action@fa7117db83c52d787ae5a89f350999701505d78e"
REVIEWED_REPORT = {
    "version": "v5.6.0",
    "commit": "61e84743356275f6ffca23b1b2f2cb945e19eb96",
}
ALLOWED = {
    "actions/checkout",
    "actions/upload-artifact",
    "github/codeql-action/upload-sarif",
    "ossf/scorecard-action",
    "step-security/harden-runner",
}


def validate(workflow):
    """Apply the pinned action's publishing constraints to the real workflow."""
    assert "env" not in workflow and "defaults" not in workflow
    permissions = workflow["permissions"]
    assert permissions == "read-all" or (
        isinstance(permissions, dict) and set(permissions.values()) <= {"read", "none"}
    )
    jobs = workflow["jobs"]
    publisher = jobs["scorecard"]
    assert publisher["runs-on"] == "ubuntu-latest"
    assert not {"env", "defaults", "container", "services"} & publisher.keys()
    assert publisher["permissions"]["id-token"] == "write"
    for job_id, job in jobs.items():
        if job_id != "scorecard":
            assert job.get("permissions", {}).get("id-token") != "write"
    for step in publisher["steps"]:
        assert "run" not in step
        assert step["uses"].split("@")[0] in ALLOWED
    scans = [
        s for s in publisher["steps"] if s["uses"].startswith("ossf/scorecard-action@")
    ]
    # A new action revision must have its emitted report contract reviewed too.
    assert [scan["uses"] for scan in scans] == [REVIEWED_ACTION]
    scan = scans[0]
    assert scan["with"]["publish_results"] == "true"
    artifact = next(
        s
        for s in publisher["steps"]
        if s["uses"].startswith("actions/upload-artifact@")
    )
    assert set(artifact["with"]["path"].split()) == {"results.json", "results.sarif"}
    assert artifact["with"]["if-no-files-found"] == "error"
    analysis = jobs["analysis"]
    assert analysis["needs"] == "scorecard"
    steps = analysis["steps"]
    download = next(
        s for s in steps if s.get("uses", "").startswith("actions/download-artifact@")
    )
    assert download["with"] == {"name": artifact["with"]["name"]}
    guard_index = next(
        i for i, s in enumerate(steps) if s.get("id") == "scorecard_completeness"
    )
    upload_index = next(
        i
        for i, s in enumerate(steps)
        if s.get("uses", "").startswith("github/codeql-action/upload-sarif@")
    )
    assert guard_index < upload_index
    assert "python3 scripts/validate_scorecard_json.py" in steps[guard_index]["run"]
    assert (
        steps[upload_index]["if"]
        == "${{ success() && steps.scorecard_completeness.outcome == 'success' }}"
    )
    assert steps[upload_index]["with"]["sarif_file"] == "results.sarif"


class ScorecardWorkflowTests(unittest.TestCase):
    """Exercise the checked-in workflow and the known unsafe arrangements."""

    def setUp(self):
        self.workflow = yaml.load(
            (ROOT / ".github/workflows/scorecards.yml").read_text(),
            Loader=yaml.BaseLoader,
        )

    def test_publishing_and_guarded_upload_contract(self):
        validate(self.workflow)

    def test_action_version_guard_and_actual_report_agree(self):
        validate(self.workflow)
        guard = runpy.run_path(str(ROOT / "scripts/validate_scorecard_json.py"))
        fixture = json.loads(
            (ROOT / "tests/fixtures/scorecard-v5.6.0.json").read_text()
        )
        self.assertEqual(guard["VERSION"], REVIEWED_REPORT)
        self.assertEqual(fixture["scorecard"], REVIEWED_REPORT)
        self.assertEqual(fixture["_provenance"]["action"], REVIEWED_ACTION)
        guard["validate"](fixture, "owner/project", "a" * 40)

    def test_unreviewed_action_revision_is_rejected(self):
        for step in self.workflow["jobs"]["scorecard"]["steps"]:
            if step["uses"].startswith("ossf/scorecard-action@"):
                step["uses"] = "ossf/scorecard-action@" + "b" * 40
        with self.assertRaises(AssertionError):
            validate(self.workflow)

    def test_custom_run_in_publishing_job_is_rejected(self):
        self.workflow["jobs"]["scorecard"]["steps"].append({"run": "python3 guard.py"})
        with self.assertRaises(AssertionError):
            validate(self.workflow)

    def test_global_write_permissions_are_rejected(self):
        self.workflow["permissions"] = {"contents": "write"}
        with self.assertRaises(AssertionError):
            validate(self.workflow)

    def test_validation_job_cannot_mint_publication_identity(self):
        self.workflow["jobs"]["analysis"]["permissions"]["id-token"] = "write"
        with self.assertRaises(AssertionError):
            validate(self.workflow)

    def test_artifact_must_be_from_this_workflow_run(self):
        for step in self.workflow["jobs"]["analysis"]["steps"]:
            if step.get("uses", "").startswith("actions/download-artifact@"):
                step["with"]["run-id"] = "1234"
        with self.assertRaises(AssertionError):
            validate(self.workflow)

    def test_upload_cannot_run_without_successful_completeness_guard(self):
        for step in self.workflow["jobs"]["analysis"]["steps"]:
            if step.get("uses", "").startswith("github/codeql-action/upload-sarif@"):
                step["if"] = "always()"
        with self.assertRaises(AssertionError):
            validate(self.workflow)

    def test_scan_must_preserve_both_original_formats(self):
        for step in self.workflow["jobs"]["scorecard"]["steps"]:
            if step["uses"].startswith("actions/upload-artifact@"):
                step["with"]["path"] = "results.sarif"
        with self.assertRaises(AssertionError):
            validate(self.workflow)


if __name__ == "__main__":
    unittest.main()
