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
