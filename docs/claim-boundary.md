# Claim Boundary

## Conclusion

Agentic Workbench는 로컬/개발 환경의 AI Agent Workflow Harness prototype이다. 자동 개발 성능, 운영 검증, 보안 완료를 주장하지 않는다.

## Allowed

- AI Agent Workflow Harness
- local/dev workflow prototype
- fixture 기반 smoke test
- planning, research, code generation, verification artifact pipeline
- verifier/replanning 구조 구현
- schema와 adapter로 두 agent layer를 연결

## Conditional

아래 표현은 실행 artifact와 검증 기록이 있을 때만 사용한다.

- 병렬 실행
- self-healing
- research-backed
- 자동 생성
- end-to-end

## Forbidden

- 완전 자동 개발
- production-ready
- 보안 검증 완료
- 실사용 검증 완료
- 코드 생성 성공률 보장
- 개발 생산성 n배
- hallucination 감소 입증
- 사람 대체
- benchmark/eval harness 완성

## Public Artifact Rules

공개 문서, README, evidence, portfolio export에는 아래를 기록하지 않는다.

- secret, token, password, API key
- `.env` 값
- raw payload
- raw prompt 전문
- raw search content 전문
- 내부 절대 경로
- private corpus 전문

## Acceptance Gates

| Gate | Purpose |
|---|---|
| Secret Redaction Gate | 로그, event, artifact에 secret-like 문자열이 평문으로 남지 않음 |
| PII/Path Redaction Gate | 이메일, 전화번호, DB URL, Bearer token, 내부 절대 경로를 public payload에서 제거 |
| Evidence Boundary Gate | research raw content를 요약 snippet으로 제한 |
| Public Artifact Exposure Gate | raw prompt, full search result, private corpus 키가 public artifact에 남지 않음 |
| Path Boundary Gate | artifact/generated file path가 run workspace 밖으로 나가지 않음 |
| Claim Copy Gate | 금지 claim 문구 정적 스캔 |
| No-Live-Call Gate | fixture 모드에서 live API 성공처럼 표현하지 않음 |
| Non-Dummy Test Gate | schema, adapter, redaction, smoke를 각각 검증 |
