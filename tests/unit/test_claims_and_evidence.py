import pytest

from packages.core.claims import assert_no_forbidden_claims, find_forbidden_claims
from packages.core.evidence import sanitize_evidence_item
from packages.core.exposure import (
    assert_no_forbidden_public_keys,
    find_forbidden_public_keys,
    sanitize_public_payload,
)


def test_claim_gate_blocks_forbidden_language():
    text = "이 프로젝트는 production-ready AI agent harness입니다."
    findings = find_forbidden_claims(text)
    assert findings[0].phrase == "production-ready"
    with pytest.raises(ValueError):
        assert_no_forbidden_claims(text)


def test_claim_gate_blocks_variants_and_multiple_findings():
    text = "Production Ready라고 쓰면 안 되고, 보안 검증 완료도 안 된다."
    findings = find_forbidden_claims(text)
    assert [finding.phrase for finding in findings] == ["production-ready", "보안 검증 완료"]


def test_claim_gate_allows_scoped_prototype_language():
    assert_no_forbidden_claims("local/dev 환경에서 검증한 AI Agent Workflow Harness prototype")


def test_evidence_sanitizer_removes_raw_content_and_redacts_secret():
    item = {
        "title": "Research",
        "url": "https://example.com",
        "content": "A" * 400 + " api_key=secret-value",
        "raw_content": "must not be copied",
    }
    sanitized = sanitize_evidence_item(item)
    assert "raw_content" not in sanitized
    assert len(sanitized["snippet"]) <= 283
    assert "secret-value" not in sanitized["snippet"]


def test_public_exposure_finds_nested_raw_artifact_fields():
    payload = {
        "safe": "summary",
        "items": [{"raw_content": "private"}, {"metadata": {"private_corpus": "internal"}}],
        "prompt_messages": [{"role": "user", "content": "full prompt"}],
    }

    findings = find_forbidden_public_keys(payload)

    assert findings == ["items[0].raw_content", "items[1].metadata.private_corpus", "prompt_messages"]
    with pytest.raises(ValueError):
        assert_no_forbidden_public_keys(payload)


def test_public_payload_sanitization_drops_forbidden_fields_and_redacts_values():
    payload = {
        "title": "Research",
        "raw_content": "do not expose",
        "nested": {
            "full_prompt": "secret prompt",
            "summary": "email user@example.com",
            "nonce": "nonce-live-sensitive",
            "signed_contract_hash": "a" * 64,
            "verifier_policy_id": "policy-local-fake",
            "key_identity_id": "key-identity-local-fake",
        },
    }

    sanitized = sanitize_public_payload(payload)

    assert "raw_content" not in sanitized
    assert "full_prompt" not in sanitized["nested"]
    assert "nonce" not in sanitized["nested"]
    assert "signed_contract_hash" not in sanitized["nested"]
    assert "verifier_policy_id" not in sanitized["nested"]
    assert "key_identity_id" not in sanitized["nested"]
    assert sanitized["nested"]["summary"] == "email [REDACTED_PII]"
