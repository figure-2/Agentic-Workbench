# Migration Plan

## Conclusion

먼저 schema와 adapter를 고정한 뒤, DIV graph와 DAACS builder를 단계적으로 추출한다. 원본 repo는 보존하고 새 프로젝트에서 integration boundary를 만든다.

## Execution Units

| id | depends_on | scope | acceptance_tests | risk_level | rollback_plan |
|---|---|---|---|---|---|
| M1 | - | 새 프로젝트 골격, README, architecture 문서 작성 | 폴더 목적과 claim boundary 명확 | low | 문서/폴더 제거 |
| M2 | M1 | 공통 schema 정의 | schema unit test 통과 | medium | schema v0 폐기 |
| M3 | M2 | DIV output adapter 작성 | DIV-style fixture -> `PlanningBlueprint` 변환 | medium | adapter 제거 |
| M4 | M2 | DAACS input/output adapter 작성 | `PlanningBlueprint -> BuildSpec -> DAACS state` 변환, endpoint/model/criteria/state key tests 통과 | medium | adapter 제거 |
| M5 | M3,M4 | fixture harness smoke 구현 | idea -> blueprint -> spec -> report 통과 | high | fixture harness 제거 |
| M6 | M5 | FastAPI fixture endpoint | `/api/v1/runs` fixture mode 응답 | medium | endpoint 비활성 |
| M7 | M6 | 원본 DIV graph 추출 | live call 없이 planner wrapper 실행 | high | 원본 DIV 유지 |
| M8 | M6 | DAACS runner boundary 분리 | offline/dry-run/live runner provider 계약 문서화, live 실행 직접 연결 금지 | high | runner boundary 문서/코드 제거 |
| M8A | M8 | `RunnerProvider` skeleton | unknown/live mode without approval blocked, offline runner regression 유지, finding evidence redacted | high | skeleton 등록 제거 |
| M8AA | M8A | `PRDPackage` / `ImplementationBrief` / `SpecApproval` gate | 승인 전 builder 호출 차단, 승인 hash mismatch 차단, PRD/brief artifact 생성, 기존 offline regression 유지 | high | 새 계약/adapter/gate 제거 |
| M8B | M8AA | dry-run runner | 실행 계획과 승인 요청만 생성, side-effect 0 | high | dry-run runner 제거 |
| M8C | M8B | gated live runner skeleton | fake runtime만 연결, approval 없으면 blocked | high | live runner 등록 비활성 |
| M8D | M8C | Solar Pro 3 provider boundary skeleton | env key 이름만 참조, approval 없으면 blocked, fake provider metrics만 기록, 실제 API 호출 0 | high | provider boundary 파일과 export 제거 |
| M8E | M8D | approval signature / nonce replay gate | unsigned approval, tampered signed approval, reused nonce blocked | high | approval signature/nonce gate 제거 |
| M8F | M8E | persistent replay store / approval verifier skeleton | restart simulation replay 차단, verifier 없으면 blocked, fake verifier metrics만 기록 | high | verifier/store boundary 제거 |
| M8G | M8F | approval verifier policy / key identity skeleton | unknown/revoked verifier/key 차단, scope mismatch 차단, future approved_at skew 차단, public output secret exposure 0 | high | verifier policy/key identity layer 제거 |
| M8H | M8G | approval policy resolver / key identity registry / durable replay boundary skeleton | unknown policy_id 차단, revoked key identity 차단, policy/key mismatch 차단, replay adapter unavailable 차단, restart replay 유지 | high | resolver/registry/durable store boundary 제거 |
| M8I | M8H | approval/replay repository boundary skeleton | approval subject snapshot hash-only 저장, replay nonce hash-only 저장, file-backed replay path/corrupt/partial/atomic fixture 차단 | high | repository boundary와 file-backed replay fixture 제거 |
| M9 | M7,M8I | 실제 end-to-end demo | 샘플 1개가 검증 리포트까지 생성 | high | demo claim 축소 |

Status note: M4 is implemented as an offline contract adapter. M8 has an offline runner boundary, a provider-boundary design, an AW-NEXT-06 `RunnerProviderRegistry` skeleton, an AW-NEXT-07A PRD/ImplementationBrief approval gate, an AW-NEXT-07B side-effect-free dry-run runner, an AW-NEXT-08 gated fake live runner skeleton, an AW-NEXT-09 fake Solar Pro 3 provider boundary skeleton, an AW-NEXT-10 structural approval signature/nonce replay gate, an AW-NEXT-11 verifier/replay store skeleton, an AW-NEXT-12 verifier policy/key identity skeleton, an AW-NEXT-13 resolver/registry/durable replay boundary skeleton, and an AW-PERSIST-02 approval/replay repository boundary skeleton with local file-backed replay fixtures. Offline, dry-run, and fake live are registered by default. Live DAACS extraction, production-grade DB persistence, production approval signing, production key registry, multi-host replay prevention, and Solar Pro 3 calls are still not implemented.

## Reuse Plan

DAACS 재사용 후보 14개:

- `daacs_workflow.py`
- `backend_subgraph.py`
- `frontend_subgraph.py`
- `orchestrator_nodes.py`
- `verification.py`
- `daacs_state.py`
- `config_loader.py`
- `cli_executor.py`
- `daacs_api_server.py`
- `daacsApi.ts`
- `WorkspacePanel.tsx`
- `InteractionConsole.tsx`
- `PreviewPanel.tsx`
- `routes.ts`

DIV 재사용 후보 15개:

- `supervisor_graph.py`
- `supervisor.py`
- `idea_graph.py`
- `plan_graph.py`
- `research_graph.py`
- `idea.py`
- `plan.py`
- `research.py`
- `plan_core/generator.py`
- `plan_core/nodes.py`
- `visual_core/generator.py`
- `llm.py`
- `config.py`
- prompts
- state 참고 자료

## Not Reused As-Is

- DIV Streamlit UI
- `st.session_state` 중심 상태 관리
- raw markdown file read/write 중심 UI
- import 시점 Tavily/Qdrant 초기화
- DAACS/Nova-Canvas 중복 API 책임
- 인증 없는 파일/로그 노출 구조
