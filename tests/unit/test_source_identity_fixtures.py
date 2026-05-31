import json
from pathlib import Path

from packages.core.claims import find_forbidden_claims
from packages.core.exposure import find_forbidden_public_keys
from packages.core.schemas import stable_contract_hash


FIXTURE_PATH = Path("tests/fixtures/source_identity_golden_path.json")


def _load_fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_source_identity_fixture_covers_required_div_and_daacs_trace_rows():
    fixture = _load_fixture()
    fixtures = fixture["fixtures"]
    covered_trace_ids = {
        trace_id
        for source_fixture in fixtures
        for trace_id in source_fixture["covered_trace_ids"]
    }

    assert fixture["fixture_id"] == "source-identity-golden-path-v1"
    assert len(fixtures) >= fixture["coverage_expectations"]["fixture_count_min"]
    assert {"DIV", "DAACS", "COMPOSITE"} <= {source_fixture["source"] for source_fixture in fixtures}
    assert covered_trace_ids == set(fixture["coverage_expectations"]["required_trace_ids"])


def test_source_identity_fixture_preserves_div_identity_signals_without_raw_source_body():
    fixture = _load_fixture()
    div = next(item for item in fixture["fixtures"] if item["fixture_id"] == "div-blueprint-identity-v1")
    identity = div["source_identity"]

    assert identity["planning_style"] == "Business"
    assert identity["toc_count"] == 7
    assert len(identity["section_titles"]) == 7
    assert identity["required_information_count"] == 6
    assert identity["seed_content_section_count"] == 1
    assert "PlanningBlueprint.features" in div["workbench_mapping"]["preserve_as"]


def test_source_identity_fixture_preserves_div_document_and_visual_signals():
    fixture = _load_fixture()
    div = next(item for item in fixture["fixtures"] if item["fixture_id"] == "div-markdown-visual-identity-v1")
    document = div["source_identity"]["document_quality_signals"]

    assert document["has_rationale"] is True
    assert document["has_toc"] is True
    assert document["has_sectioned_markdown"] is True
    assert {"mermaid_flowchart", "comparison_table"} <= set(document["visual_artifact_types"])
    assert "PlanningBlueprint.visual_artifacts" in div["workbench_mapping"]["preserve_as"]
    assert "PRDPackage.evidence_summary" in div["workbench_mapping"]["preserve_as"]


def test_source_identity_fixture_preserves_daacs_identity_signals_without_live_execution():
    fixture = _load_fixture()
    daacs = next(item for item in fixture["fixtures"] if item["source"] == "DAACS")
    identity = daacs["source_identity"]
    runner = identity["runner_config_signals"]
    verification = identity["verification_signals"]

    assert identity["role_split"] == ["orchestrator", "backend", "frontend", "verifier"]
    assert identity["backend_frontend_split"]["api_contract_required"] is True
    assert runner["cli_assistant_type"] == "claude_code"
    assert runner["parallel_execution_source_value"] is True
    assert runner["current_workbench_claim"] == "planned_split_only"
    assert verification["has_coder_verifier_loop_identity"] is True
    assert verification["has_replanning_identity"] is True
    assert "RunnerPlan.planned_actions" in daacs["workbench_mapping"]["preserve_as"]
    assert "CLI subprocess execution" in daacs["workbench_mapping"]["defer_or_reject"]


def test_source_identity_fixture_is_public_safe_and_hash_stable():
    fixture = _load_fixture()
    serialized = json.dumps(fixture, ensure_ascii=True, sort_keys=True)

    assert find_forbidden_public_keys(fixture) == []
    assert find_forbidden_claims(serialized) == []
    assert "system_prompt" not in serialized
    assert "provider_payload" not in serialized
    assert "file_body" not in serialized
    assert "raw_prompt" not in serialized
    assert "token=" not in serialized
    assert fixture["claim_boundary"]["direct_original_runtime_called"] is False
    assert fixture["claim_boundary"]["live_provider_called"] is False
    assert stable_contract_hash(fixture) == stable_contract_hash(_load_fixture())
