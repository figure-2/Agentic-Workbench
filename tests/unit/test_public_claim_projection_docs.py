from pathlib import Path

from packages.core.claims import find_forbidden_claims
from packages.core.exposure import find_forbidden_public_keys


ROOT = Path(__file__).resolve().parents[2]
README_PATH = ROOT / "README.md"
CLAIM_BOUNDARY_PATH = ROOT / "docs" / "claim-boundary.md"
METRICS_PATH = ROOT / "docs" / "metrics.md"
ARCHITECTURE_PATH = ROOT / "docs" / "architecture.md"
PARITY_00_PATH = ROOT / "docs" / "evals" / "aw-parity-00-public-api-fixture-boundary.md"
PARITY_01A_PATH = ROOT / "docs" / "evals" / "aw-parity-01a-source-identity-fixtures.md"
PARITY_01B_PATH = ROOT / "docs" / "evals" / "aw-parity-01b-source-identity-golden-path.md"
PARITY_01C_PATH = ROOT / "docs" / "evals" / "aw-parity-01c-trace-claim-projection.md"
PERSIST_03_PATH = ROOT / "docs" / "evals" / "aw-persist-03-runner-report-audit-repositories.md"
PERSIST_04_PATH = ROOT / "docs" / "evals" / "aw-persist-04-sqlite-runner-report-audit.md"
PERSIST_02_PATH = ROOT / "docs" / "evals" / "aw-persist-02-approval-replay-repositories.md"
PERSIST_05_PATH = ROOT / "docs" / "evals" / "aw-persist-05-sqlite-approval-replay.md"
PERSIST_06_PATH = ROOT / "docs" / "evals" / "aw-persist-06-approval-replay-wiring.md"
PERSIST_07_PATH = ROOT / "docs" / "evals" / "aw-persist-07-canonical-approval-persistence.md"
PERSIST_08_PATH = ROOT / "docs" / "evals" / "aw-persist-08-sqlite-run-artifact.md"
API_01_PATH = ROOT / "docs" / "evals" / "aw-api-01-sanitized-approval-admission-api.md"
API_02_PATH = ROOT / "docs" / "evals" / "aw-api-02-sqlite-admission-repository-wiring.md"
API_03_PATH = ROOT / "docs" / "evals" / "aw-api-03-evidence-read-model-api.md"
API_04_PATH = ROOT / "docs" / "evals" / "aw-api-04-fixture-evidence-persistence.md"
API_05_PATH = ROOT / "docs" / "evals" / "aw-api-05-run-artifact-read-api.md"
LIVE_00_PATH = ROOT / "docs" / "evals" / "aw-live-00-live-open-policy-gate.md"
DEMO_03_PATH = ROOT / "docs" / "evals" / "aw-demo-03-static-ui-shell.md"
LIVE_01_PATH = ROOT / "docs" / "evals" / "aw-live-01-disabled-solar-provider-adapter.md"
LIVE_02_PATH = ROOT / "docs" / "evals" / "aw-live-02-solar-contract-fixtures.md"
LIVE_03_PATH = ROOT / "docs" / "evals" / "aw-live-03-provider-envelope-read-model.md"
LIVE_04_PATH = ROOT / "docs" / "evals" / "aw-live-04-provider-envelope-admission.md"
LIVE_05_PATH = ROOT / "docs" / "evals" / "aw-live-05-provider-envelope-api-hook.md"
LIVE_06_PATH = ROOT / "docs" / "evals" / "aw-live-06-operator-approval-envelope.md"
LIVE_07_PATH = ROOT / "docs" / "evals" / "aw-live-07-live-provider-dry-admission-runbook.md"
LIVE_07_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-07-live-provider-dry-admission.md"
LIVE_07_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-07-live-provider-dry-admission-runbook.md"
)
LIVE_08_PATH = ROOT / "docs" / "evals" / "aw-live-08-manual-provider-test-proposal.md"
LIVE_08_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-08-manual-provider-test-proposal.md"
LIVE_08_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-08-manual-provider-test-proposal.md"
)
LIVE_09_PATH = ROOT / "docs" / "evals" / "aw-live-09-disabled-manual-provider-test-executor.md"
LIVE_09_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-09-disabled-manual-provider-test-executor.md"
)
LIVE_09_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-09-disabled-manual-provider-test-executor.md"
)
LIVE_10_PATH = ROOT / "docs" / "evals" / "aw-live-10-one-shot-live-permission-contract.md"
LIVE_10_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-10-one-shot-live-permission-contract.md"
)
LIVE_10_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-10-one-shot-live-permission-contract.md"
)
LIVE_11_PATH = ROOT / "docs" / "evals" / "aw-live-11-preflight-audit-bundle.md"
LIVE_11_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-11-preflight-audit-bundle.md"
LIVE_11_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-11-preflight-audit-bundle.md"
)
LIVE_12_PATH = ROOT / "docs" / "evals" / "aw-live-12-readiness-decision-record.md"
LIVE_12_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-12-readiness-decision-record.md"
LIVE_12_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-12-readiness-decision-record.md"
)
LIVE_13_PATH = ROOT / "docs" / "evals" / "aw-live-13-review-packet.md"
LIVE_13_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-13-review-packet.md"
LIVE_13_WORK_ORDER_PATH = ROOT / "docs" / "work-orders" / "aw-live-13-review-packet.md"
LIVE_14_PATH = ROOT / "docs" / "evals" / "aw-live-14-review-packet-export-read-model.md"
LIVE_14_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-14-review-packet-export-read-model.md"
)
LIVE_14_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-14-review-packet-export-read-model.md"
)
LIVE_15_PATH = ROOT / "docs" / "evals" / "aw-live-15-handoff-packet.md"
LIVE_15_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-15-handoff-packet.md"
LIVE_15_WORK_ORDER_PATH = ROOT / "docs" / "work-orders" / "aw-live-15-handoff-packet.md"
LIVE_16_PATH = ROOT / "docs" / "evals" / "aw-live-16-operator-opt-in-checklist.md"
LIVE_16_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-16-operator-opt-in-checklist.md"
)
LIVE_16_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-16-operator-opt-in-checklist.md"
)
LIVE_17_PATH = ROOT / "docs" / "evals" / "aw-live-17-sealed-pre-execution-packet.md"
LIVE_17_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-17-sealed-pre-execution-packet.md"
)
LIVE_17_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-17-sealed-pre-execution-packet.md"
)
LIVE_18_PATH = ROOT / "docs" / "evals" / "aw-live-18-arming-record.md"
LIVE_18_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-18-arming-record.md"
LIVE_18_WORK_ORDER_PATH = ROOT / "docs" / "work-orders" / "aw-live-18-arming-record.md"
LIVE_19_PATH = ROOT / "docs" / "evals" / "aw-live-19-release-proposal.md"
LIVE_19_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-19-release-proposal.md"
LIVE_19_WORK_ORDER_PATH = ROOT / "docs" / "work-orders" / "aw-live-19-release-proposal.md"
LIVE_20_PATH = ROOT / "docs" / "evals" / "aw-live-20-final-release-packet.md"
LIVE_20_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-20-final-release-packet.md"
LIVE_20_WORK_ORDER_PATH = ROOT / "docs" / "work-orders" / "aw-live-20-final-release-packet.md"
LIVE_21_PATH = ROOT / "docs" / "evals" / "aw-live-21-execution-switch.md"
LIVE_21_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-21-execution-switch.md"
LIVE_21_WORK_ORDER_PATH = ROOT / "docs" / "work-orders" / "aw-live-21-execution-switch.md"
LIVE_22_PATH = ROOT / "docs" / "evals" / "aw-live-22-executor-preflight.md"
LIVE_22_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-22-executor-preflight.md"
LIVE_22_WORK_ORDER_PATH = ROOT / "docs" / "work-orders" / "aw-live-22-executor-preflight.md"
LIVE_23_PATH = ROOT / "docs" / "evals" / "aw-live-23-executor-dispatch-record.md"
LIVE_23_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-23-executor-dispatch-record.md"
LIVE_23_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-23-executor-dispatch-record.md"
)
LIVE_24_PATH = ROOT / "docs" / "evals" / "aw-live-24-invocation-receipt.md"
LIVE_24_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-24-invocation-receipt.md"
LIVE_24_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-24-invocation-receipt.md"
)
LIVE_25_PATH = ROOT / "docs" / "evals" / "aw-live-25-post-invocation-audit.md"
LIVE_25_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-25-post-invocation-audit.md"
LIVE_25_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-25-post-invocation-audit.md"
)
LIVE_26_PATH = ROOT / "docs" / "evals" / "aw-live-26-completion-summary.md"
LIVE_26_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-26-completion-summary.md"
LIVE_26_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-26-completion-summary.md"
)
LIVE_27_PATH = ROOT / "docs" / "evals" / "aw-live-27-closeout-record.md"
LIVE_27_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-27-closeout-record.md"
LIVE_27_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-27-closeout-record.md"
)
LIVE_28_PATH = ROOT / "docs" / "evals" / "aw-live-28-operator-handback.md"
LIVE_28_RUNBOOK_PATH = ROOT / "docs" / "runbooks" / "aw-live-28-operator-handback.md"
LIVE_28_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-28-operator-handback.md"
)
LIVE_29_PATH = ROOT / "docs" / "evals" / "aw-live-29-operator-decision-packet.md"
LIVE_29_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-29-operator-decision-packet.md"
)
LIVE_29_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-29-operator-decision-packet.md"
)
LIVE_30_PATH = ROOT / "docs" / "evals" / "aw-live-30-operator-release-attestation.md"
LIVE_30_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-30-operator-release-attestation.md"
)
LIVE_30_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-30-operator-release-attestation.md"
)
LIVE_31_PATH = ROOT / "docs" / "evals" / "aw-live-31-release-authorization-seal.md"
LIVE_31_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-31-release-authorization-seal.md"
)
LIVE_31_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-31-release-authorization-seal.md"
)
LIVE_32_PATH = ROOT / "docs" / "evals" / "aw-live-32-execution-authorization-capsule.md"
LIVE_32_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-32-execution-authorization-capsule.md"
)
LIVE_32_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-32-execution-authorization-capsule.md"
)
LIVE_33_PATH = (
    ROOT / "docs" / "evals" / "aw-live-33-execution-capsule-export-read-model.md"
)
LIVE_33_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-33-execution-capsule-export-read-model.md"
)
LIVE_33_WORK_ORDER_PATH = (
    ROOT
    / "docs"
    / "work-orders"
    / "aw-live-33-execution-capsule-export-read-model.md"
)
LIVE_34_PATH = ROOT / "docs" / "evals" / "aw-live-34-execution-capsule-handoff-packet.md"
LIVE_34_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-34-execution-capsule-handoff-packet.md"
)
LIVE_34_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-34-execution-capsule-handoff-packet.md"
)
LIVE_35_PATH = ROOT / "docs" / "evals" / "aw-live-35-execution-capsule-operator-review.md"
LIVE_35_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-35-execution-capsule-operator-review.md"
)
LIVE_35_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-35-execution-capsule-operator-review.md"
)
LIVE_36_PATH = ROOT / "docs" / "evals" / "aw-live-36-execution-capsule-operator-decision.md"
LIVE_36_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-36-execution-capsule-operator-decision.md"
)
LIVE_36_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-36-execution-capsule-operator-decision.md"
)
LIVE_37_PATH = (
    ROOT / "docs" / "evals" / "aw-live-37-execution-capsule-release-attestation.md"
)
LIVE_37_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-37-execution-capsule-release-attestation.md"
)
LIVE_37_WORK_ORDER_PATH = (
    ROOT
    / "docs"
    / "work-orders"
    / "aw-live-37-execution-capsule-release-attestation.md"
)
LIVE_38_PATH = (
    ROOT / "docs" / "evals" / "aw-live-38-execution-capsule-release-seal.md"
)
LIVE_38_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-38-execution-capsule-release-seal.md"
)
LIVE_38_WORK_ORDER_PATH = (
    ROOT / "docs" / "work-orders" / "aw-live-38-execution-capsule-release-seal.md"
)
LIVE_39_PATH = (
    ROOT / "docs" / "evals" / "aw-live-39-execution-capsule-final-authorization.md"
)
LIVE_39_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-39-execution-capsule-final-authorization.md"
)
LIVE_39_WORK_ORDER_PATH = (
    ROOT
    / "docs"
    / "work-orders"
    / "aw-live-39-execution-capsule-final-authorization.md"
)
LIVE_40_PATH = (
    ROOT
    / "docs"
    / "evals"
    / "aw-live-40-execution-capsule-authz-export-read-model.md"
)
LIVE_40_RUNBOOK_PATH = (
    ROOT
    / "docs"
    / "runbooks"
    / "aw-live-40-execution-capsule-authz-export-read-model.md"
)
LIVE_40_WORK_ORDER_PATH = (
    ROOT
    / "docs"
    / "work-orders"
    / "aw-live-40-execution-capsule-authz-export-read-model.md"
)
LIVE_41_PATH = (
    ROOT / "docs" / "evals" / "aw-live-41-execution-capsule-authz-handoff-packet.md"
)
LIVE_41_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-41-execution-capsule-authz-handoff-packet.md"
)
LIVE_41_WORK_ORDER_PATH = (
    ROOT
    / "docs"
    / "work-orders"
    / "aw-live-41-execution-capsule-authz-handoff-packet.md"
)
LIVE_42_PATH = (
    ROOT / "docs" / "evals" / "aw-live-42-execution-capsule-authz-operator-review.md"
)
LIVE_42_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-42-execution-capsule-authz-operator-review.md"
)
LIVE_42_WORK_ORDER_PATH = (
    ROOT
    / "docs"
    / "work-orders"
    / "aw-live-42-execution-capsule-authz-operator-review.md"
)
LIVE_43_PATH = (
    ROOT / "docs" / "evals" / "aw-live-43-execution-capsule-authz-operator-decision.md"
)
LIVE_43_RUNBOOK_PATH = (
    ROOT / "docs" / "runbooks" / "aw-live-43-execution-capsule-authz-operator-decision.md"
)
LIVE_43_WORK_ORDER_PATH = (
    ROOT
    / "docs"
    / "work-orders"
    / "aw-live-43-execution-capsule-authz-operator-decision.md"
)
LIVE_44_PATH = (
    ROOT
    / "docs"
    / "evals"
    / "aw-live-44-execution-capsule-authz-release-attestation.md"
)
LIVE_44_RUNBOOK_PATH = (
    ROOT
    / "docs"
    / "runbooks"
    / "aw-live-44-execution-capsule-authz-release-attestation.md"
)
LIVE_44_WORK_ORDER_PATH = (
    ROOT
    / "docs"
    / "work-orders"
    / "aw-live-44-execution-capsule-authz-release-attestation.md"
)

PUBLIC_CLAIM_DOCS = [
    README_PATH,
    CLAIM_BOUNDARY_PATH,
    METRICS_PATH,
    ARCHITECTURE_PATH,
    PARITY_00_PATH,
    PARITY_01A_PATH,
    PARITY_01B_PATH,
    PARITY_01C_PATH,
    PERSIST_02_PATH,
    PERSIST_03_PATH,
    PERSIST_04_PATH,
    PERSIST_05_PATH,
    PERSIST_06_PATH,
    PERSIST_07_PATH,
    PERSIST_08_PATH,
    API_01_PATH,
    API_02_PATH,
    API_03_PATH,
    API_04_PATH,
    API_05_PATH,
    LIVE_00_PATH,
    DEMO_03_PATH,
    LIVE_01_PATH,
    LIVE_02_PATH,
    LIVE_03_PATH,
    LIVE_04_PATH,
    LIVE_05_PATH,
    LIVE_06_PATH,
    LIVE_07_PATH,
    LIVE_07_RUNBOOK_PATH,
    LIVE_07_WORK_ORDER_PATH,
    LIVE_08_PATH,
    LIVE_08_RUNBOOK_PATH,
    LIVE_08_WORK_ORDER_PATH,
    LIVE_09_PATH,
    LIVE_09_RUNBOOK_PATH,
    LIVE_09_WORK_ORDER_PATH,
    LIVE_10_PATH,
    LIVE_10_RUNBOOK_PATH,
    LIVE_10_WORK_ORDER_PATH,
    LIVE_11_PATH,
    LIVE_11_RUNBOOK_PATH,
    LIVE_11_WORK_ORDER_PATH,
    LIVE_12_PATH,
    LIVE_12_RUNBOOK_PATH,
    LIVE_12_WORK_ORDER_PATH,
    LIVE_13_PATH,
    LIVE_13_RUNBOOK_PATH,
    LIVE_13_WORK_ORDER_PATH,
    LIVE_14_PATH,
    LIVE_14_RUNBOOK_PATH,
    LIVE_14_WORK_ORDER_PATH,
    LIVE_15_PATH,
    LIVE_15_RUNBOOK_PATH,
    LIVE_15_WORK_ORDER_PATH,
    LIVE_16_PATH,
    LIVE_16_RUNBOOK_PATH,
    LIVE_16_WORK_ORDER_PATH,
    LIVE_17_PATH,
    LIVE_17_RUNBOOK_PATH,
    LIVE_17_WORK_ORDER_PATH,
    LIVE_18_PATH,
    LIVE_18_RUNBOOK_PATH,
    LIVE_18_WORK_ORDER_PATH,
    LIVE_19_PATH,
    LIVE_19_RUNBOOK_PATH,
    LIVE_19_WORK_ORDER_PATH,
    LIVE_20_PATH,
    LIVE_20_RUNBOOK_PATH,
    LIVE_20_WORK_ORDER_PATH,
    LIVE_21_PATH,
    LIVE_21_RUNBOOK_PATH,
    LIVE_21_WORK_ORDER_PATH,
    LIVE_22_PATH,
    LIVE_22_RUNBOOK_PATH,
    LIVE_22_WORK_ORDER_PATH,
    LIVE_23_PATH,
    LIVE_23_RUNBOOK_PATH,
    LIVE_23_WORK_ORDER_PATH,
    LIVE_24_PATH,
    LIVE_24_RUNBOOK_PATH,
    LIVE_24_WORK_ORDER_PATH,
    LIVE_25_PATH,
    LIVE_25_RUNBOOK_PATH,
    LIVE_25_WORK_ORDER_PATH,
    LIVE_26_PATH,
    LIVE_26_RUNBOOK_PATH,
    LIVE_26_WORK_ORDER_PATH,
    LIVE_27_PATH,
    LIVE_27_RUNBOOK_PATH,
    LIVE_27_WORK_ORDER_PATH,
    LIVE_28_PATH,
    LIVE_28_RUNBOOK_PATH,
    LIVE_28_WORK_ORDER_PATH,
    LIVE_29_PATH,
    LIVE_29_RUNBOOK_PATH,
    LIVE_29_WORK_ORDER_PATH,
    LIVE_30_PATH,
    LIVE_30_RUNBOOK_PATH,
    LIVE_30_WORK_ORDER_PATH,
    LIVE_31_PATH,
    LIVE_31_RUNBOOK_PATH,
    LIVE_31_WORK_ORDER_PATH,
    LIVE_32_PATH,
    LIVE_32_RUNBOOK_PATH,
    LIVE_32_WORK_ORDER_PATH,
    LIVE_33_PATH,
    LIVE_33_RUNBOOK_PATH,
    LIVE_33_WORK_ORDER_PATH,
    LIVE_34_PATH,
    LIVE_34_RUNBOOK_PATH,
    LIVE_34_WORK_ORDER_PATH,
    LIVE_35_PATH,
    LIVE_35_RUNBOOK_PATH,
    LIVE_35_WORK_ORDER_PATH,
    LIVE_36_PATH,
    LIVE_36_RUNBOOK_PATH,
    LIVE_36_WORK_ORDER_PATH,
    LIVE_37_PATH,
    LIVE_37_RUNBOOK_PATH,
    LIVE_37_WORK_ORDER_PATH,
    LIVE_38_PATH,
    LIVE_38_RUNBOOK_PATH,
    LIVE_38_WORK_ORDER_PATH,
    LIVE_39_PATH,
    LIVE_39_RUNBOOK_PATH,
    LIVE_39_WORK_ORDER_PATH,
    LIVE_40_PATH,
    LIVE_40_RUNBOOK_PATH,
    LIVE_40_WORK_ORDER_PATH,
    LIVE_41_PATH,
    LIVE_41_RUNBOOK_PATH,
    LIVE_41_WORK_ORDER_PATH,
    LIVE_42_PATH,
    LIVE_42_RUNBOOK_PATH,
    LIVE_42_WORK_ORDER_PATH,
    LIVE_43_PATH,
    LIVE_43_RUNBOOK_PATH,
    LIVE_43_WORK_ORDER_PATH,
    LIVE_44_PATH,
    LIVE_44_RUNBOOK_PATH,
    LIVE_44_WORK_ORDER_PATH,
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _public_safe_block(text: str) -> str:
    start = "<!-- public-portfolio-safe-start -->"
    end = "<!-- public-portfolio-safe-end -->"
    return text.split(start, 1)[1].split(end, 1)[0]


def test_aw_parity_01c_public_projection_wording_is_claim_safe():
    doc = _read(PARITY_01C_PATH)
    block = _public_safe_block(doc)

    assert find_forbidden_claims(block) == []
    assert find_forbidden_public_keys({"portfolio_safe_wording": block}) == []
    assert "local/dev" in block
    assert "prototype" in block
    assert "fixture-based" in block
    assert "dry-run" in block


def test_aw_parity_01c_trace_rows_link_to_golden_path_smoke_test():
    doc = _read(PARITY_01C_PATH)
    required_trace_ids = {
        "TR-DIV-01",
        "TR-DIV-02",
        "TR-DIV-03",
        "TR-DIV-04",
        "TR-DAACS-01",
        "TR-DAACS-03",
        "TR-DAACS-04",
        "TR-DAACS-07",
    }

    for trace_id in required_trace_ids:
        assert trace_id in doc
    assert doc.count("test_source_identity_fixture_runs_through_golden_path_without_live_side_effects") >= 1


def test_public_claim_docs_remain_scanner_safe_after_parity_projection():
    findings_by_path = {
        path.as_posix(): find_forbidden_claims(_read(path)) for path in PUBLIC_CLAIM_DOCS
    }

    assert findings_by_path == {path.as_posix(): [] for path in PUBLIC_CLAIM_DOCS}
