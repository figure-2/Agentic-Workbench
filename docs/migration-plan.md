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
| M8J | M8I | canonical approval persistence service boundary | provider/live canonical approval row 선행 저장, persisted hash 일치, missing service 차단, raw authorization material 저장 0 | high | service boundary 제거, repository factory wiring 상태로 복귀 |
| M8K | M8J | sanitized fake admission API/service wiring | provider/live fake admission API가 canonical approval persistence service 사용, fixture/synthetic path 분리, raw auth public response 0 | high | API/service wiring 제거, AW-PERSIST-07 유지 |
| M8L | M8K | SQLite-backed fake admission API wiring | 명시적 SQLite approval/replay repository 선택, API 요청 간 reused nonce 차단, 손상/사용불가 store는 fake 호출 전 차단, fixture path durable write 0 | high | API repository backend wiring 제거, AW-API-01 request-scoped memory demo 유지 |
| M8M | M8L | sanitized evidence read-model API | runner/report/audit 및 approval/replay 저장 evidence를 raw body 없이 조회, 손상 store blocked, provider/runtime call 0 | high | evidence read-model API 제거, AW-API-02 상태 유지 |
| M8N | M8M | fixture evidence persistence write path | 명시적 evidence repository가 있을 때 `/api/v1/runs` fixture 결과를 runner/report/audit projection으로 저장, read-model API로 조회, fixture approval/replay durable write 0 | high | evidence write service/API 연결 제거, AW-API-03 상태 유지 |
| M8O | M8N | repository-backed run/artifact read API | 저장된 artifact projection rows를 `/api/v1/runs/{run_id}`와 `/api/v1/runs/{run_id}/artifacts`에서 raw body 없이 조회, cross-run leakage 0, corrupted store blocked | high | run/artifact read API 제거, AW-API-04 상태 유지 |
| M8P | M8O | SQLite-backed canonical run/artifact repository | `/api/v1/runs`가 sanitized RunSessionRecord/ArtifactRecord를 별도 canonical store에 저장, canonical GET이 prompt_contract_hash/stage/status/idea_summary 반환, evidence/admission DB 혼동 0 | high | canonical run/artifact SQLite adapter와 API 연결 제거, AW-API-05 상태 유지 |
| M8Q | M8P | canonical run/evidence composed read model | canonical run state를 primary로 두고 optional evidence summary를 별도 section으로 조합, missing evidence는 canonical 조회 유지, corrupted evidence는 evidence section만 blocked, raw body 노출 0 | high | composition 제거, M8P canonical read API 유지 |
| M8R | M8Q | local service-shaped demo | live/provider 호출 없이 idea -> artifacts -> dry-run plan -> verification -> composed read model까지 샘플 1개를 재현 | medium | demo route/script/docs 제거, M8Q 유지 |
| M8S | M8R | minimal run status surface | composed read model을 사람이 읽을 수 있는 Markdown/CLI status surface로 렌더링, raw leakage 0, provider/runtime call 0 | medium | status surface script/docs/tests 제거, M8R 유지 |
| M8T | M8S | live-open policy gate | Solar Pro 3 또는 DAACS runtime 호출 전 approval policy, replay, cost/quota, timeout, sandbox, write allowlist, rollback, redaction, audit checklist를 ADR/test로 고정 | high | live-open policy 제거, all live calls remain blocked |
| M8U | M8S,M8T | static UI shell | 같은 public summary 위에 static HTML shell 추가, live policy closed/eligible 표시, raw leakage 0, provider/runtime call 0 | medium | static UI shell 제거, M8S 유지 |
| M9 | M7,M8T,M8U | 실제 end-to-end demo | live-open 조건을 만족한 샘플 1개가 검증 리포트까지 생성 | high | demo claim 축소 |

Status note: M4 is implemented as an offline contract adapter. M8 has an offline runner boundary, a provider-boundary design, an AW-NEXT-06 `RunnerProviderRegistry` skeleton, an AW-NEXT-07A PRD/ImplementationBrief approval gate, an AW-NEXT-07B side-effect-free dry-run runner, an AW-NEXT-08 gated fake live runner skeleton, an AW-NEXT-09 fake Solar Pro 3 provider boundary skeleton, an AW-NEXT-10 structural approval signature/nonce replay gate, an AW-NEXT-11 verifier/replay store skeleton, an AW-NEXT-12 verifier policy/key identity skeleton, an AW-NEXT-13 resolver/registry/durable replay boundary skeleton, an AW-PERSIST-02 approval/replay repository boundary skeleton with local file-backed replay fixtures, an AW-PERSIST-06 optional SQLite-backed replay wiring path for fake admission, an AW-PERSIST-07 canonical approval persistence service before replay claim, an AW-API-01 sanitized fake admission API demo path, AW-API-02 SQLite-backed fake admission API wiring, AW-API-03 sanitized evidence read-model API skeleton, AW-API-04 optional fixture evidence persistence, AW-API-05 repository-backed run/artifact read API skeleton, AW-PERSIST-08 SQLite-backed canonical run/artifact repository skeleton, AW-API-06 canonical run/evidence composed read model, AW-DEMO-01 local service-shaped demo, AW-DEMO-02 minimal run status surface, AW-LIVE-00 fail-closed live-open policy gate, and AW-DEMO-03 static UI shell. Offline, dry-run, and fake live are registered by default. Live DAACS extraction, production-grade DB persistence, production approval signing, production key registry, multi-host replay prevention, Solar Pro 3 calls, and target runtime calls are still not implemented.

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
