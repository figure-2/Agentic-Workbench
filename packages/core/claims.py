"""Claim boundary checks for public-facing artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import re


FORBIDDEN_CLAIMS = [
    "완전 자동 개발",
    "완전자동개발",
    "완성된 자동 개발 플랫폼",
    "실제 앱 자동 구현 완료",
    "실제 자동 개발 성공",
    "production-ready",
    "프로덕션 준비",
    "production generated app success",
    "generated app production success",
    "보안 검증 완료",
    "실사용 검증 완료",
    "개발 생산성 n배",
    "생산성 향상 입증",
    "코드 생성 성공률 보장",
    "hallucination 감소 입증",
    "사람 대체",
    "benchmark/eval harness 완성",
    "eval harness 완성",
    "사람을 대체",
    "live provider success",
    "real provider call success",
    "Solar Pro 3 live success",
    "Solar Pro 3 live call success",
    "real DAACS execution",
    "DAACS live execution",
    "actual DAACS execution",
    "real source-runtime execution",
    "source runtime direct integration",
    "원본 runtime 재현",
    "원본 런타임 재현",
    "실제 DAACS 실행",
    "DAACS live 실행",
    "실제 source runtime 실행",
]


@dataclass(frozen=True, slots=True)
class ClaimFinding:
    phrase: str
    index: int


def _claim_pattern(phrase: str) -> re.Pattern[str]:
    escaped = re.escape(phrase)
    escaped = escaped.replace(r"\-", r"[\s_-]+")
    escaped = escaped.replace(r"\ ", r"[\s_-]+")
    return re.compile(escaped, re.IGNORECASE)


def find_forbidden_claims(text: str) -> list[ClaimFinding]:
    """Return forbidden claim occurrences in a case-insensitive scan."""
    findings: list[ClaimFinding] = []
    for phrase in FORBIDDEN_CLAIMS:
        for match in _claim_pattern(phrase).finditer(text):
            findings.append(ClaimFinding(phrase=phrase, index=match.start()))
    return sorted(findings, key=lambda finding: finding.index)


def assert_no_forbidden_claims(text: str) -> None:
    """Raise if public text contains unsupported claim language."""
    findings = find_forbidden_claims(text)
    if findings:
        phrases = ", ".join(finding.phrase for finding in findings)
        raise ValueError(f"forbidden claim language found: {phrases}")
