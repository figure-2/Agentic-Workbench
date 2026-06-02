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
| M8V | M8T,M8U | disabled Solar Pro 3 provider adapter | live provider adapter skeleton 등록 가능, 기본 실행 blocked, env value read 0, timeout/cost/quota missing blocked, fake/live path 분리, API call 0 | high | provider adapter skeleton 제거, M8T 유지 |
| M8W | M8V | Solar Pro 3 contract fixtures | request는 prompt_contract_hash 기반 fixture만 사용, response는 sanitized summary/hash만 포함, timeout/cost/quota 누락 blocked, API call 0 | high | contract fixture 제거, M8V 유지 |
| M8X | M8W | provider envelope persistence/read model | request/response contract hash 저장, public read model은 hash/count/status만 반환, corrupted store blocked, API call 0 | high | provider envelope persistence/read-model 제거, M8W 유지 |
| M8Y | M8X | provider envelope admission service | disabled adapter 호출 전 envelope save/read/hash match 검증, missing service/store/hash mismatch blocked, API call 0 | high | admission service wiring 제거, M8X 유지 |
| M8Z | M8Y | provider envelope API/read-model hook | API/demo 경로에서 optional provider envelope precheck 사용, public response는 status/hash/count만 반환, corrupted store blocked, API call 0 | high | API/read-model hook 제거, M8Y 유지 |
| M8ZA | M8Z | provider precheck operator approval envelope | precheck 전 cost/timeout/quota/readiness summary hash를 operator approval envelope로 승인, missing approval blocked, API call 0 | high | operator approval envelope 제거, M8Z 유지 |
| M8ZB | M8ZA | live provider dry-admission runbook | live 호출 전 수동 체크리스트 문서화, 비용/timeout/quota/rollback/operator 승인 조건 명시, API/demo는 dry-admission 상태만 표시, API call 0 | high | runbook/checklist projection 제거, M8ZA 유지 |
| M8ZC | M8ZB | manual provider test proposal gate | 별도 proposal 승인 없으면 blocked, proposal은 run_id/prompt_contract_hash/cost/timeout/quota/rollback/abort criteria 포함, 기본 실행 disabled, API call 0 | high | proposal gate 제거, M8ZB 유지 |
| M8ZD | M8ZC | disabled manual provider test executor | proposal approved_disabled 후에도 executor blocked, executor flag 있어도 disabled, public projection은 status/reason/planned_call_hash만 반환, API call 0 | high | executor boundary 제거, M8ZC 유지 |
| M8ZE | M8ZD | one-shot permission contract | run/proposal/planned-call/cost/timeout/quota/rollback/abort/expiry 후보를 hash/status/reason/expiry/count로만 노출, API call 0 | high | permission contract 제거, M8ZD 유지 |
| M8ZF | M8ZE | preflight audit bundle | proposal/executor/permission/checklist/no-call counters를 hash/status/reason/count로만 묶어 조회, API call 0 | high | preflight bundle 제거, M8ZE 유지 |
| M8ZG | M8ZF | readiness decision record | preflight hash 기반 approve/reject/defer decision을 hash/status/reason/count로만 노출, execution permission 0, API call 0 | high | readiness decision 제거, M8ZF 유지 |
| M8ZH | M8ZG | review packet | policy summary / preflight audit / readiness decision을 hash/status/reason/count로만 묶어 조회, execution permission 0, API call 0 | high | review packet 제거, M8ZG 유지 |
| M8ZI | M8ZH | review packet export/read-model | review packet을 hash/status/reason/count row로 저장/조회, packet hash mismatch blocked, execution permission 0, API call 0 | high | export/read-model 제거, M8ZH 유지 |
| M8ZJ | M8ZI | final no-call handoff packet | policy/preflight/readiness/review/export evidence를 hash/status/reason/count로만 묶어 조회, export/handoff hash mismatch blocked, execution permission 0, API call 0 | high | handoff packet 제거, M8ZI 유지 |
| M8ZK | M8ZJ | first live-call operator opt-in checklist | handoff packet hash가 존재하고 opt-in payload hash가 일치해야 하며, opt-in 후에도 execution permission 0, API call 0 | high | opt-in checklist 제거, M8ZJ 유지 |
| M8ZL | M8ZK | sealed pre-execution packet | handoff/opt-in/cost/timeout/quota/rollback/abort hash를 하나의 sealed packet으로 묶되 execution permission 0, API call 0 | high | sealed packet 제거, M8ZK 유지 |
| M8ZM | M8ZL | no-call arming record | sealed packet/operator/expiry/rollback/abort policy hash를 arming record로 묶되 execution permission 0, API call 0 | high | arming record 제거, M8ZL 유지 |
| M8ZN | M8ZM | no-call release proposal | arming record/operator/release window/rollback hash를 release proposal로 묶되 execution permission 0, API call 0 | high | release proposal 제거, M8ZM 유지 |
| M8ZO | M8ZN | no-call final release packet | release proposal/arming record/operator/release window/rollback hash를 final packet으로 묶되 execution permission 0, API call 0 | high | final release packet 제거, M8ZN 유지 |
| M8ZP | M8ZO | disabled first-call execution switch | final release packet hash와 switch-enable hash를 묶되 enable flag가 있어도 execution permission 0, API call 0 | high | execution switch 제거, M8ZO 유지 |
| M8ZQ | M8ZP | disabled first-call executor preflight | execution switch/final release/no-call counter hash를 묶되 preflight 후에도 execution permission 0, API call 0 | high | executor preflight 제거, M8ZP 유지 |
| M8ZR | M8ZQ | disabled first-call executor dispatch record | executor preflight/planned dispatch/no-call counter hash를 묶되 dispatch record 후에도 execution permission 0, API call 0 | high | dispatch record 제거, M8ZQ 유지 |
| M8ZS | M8ZR | disabled first-call invocation receipt | dispatch record/result placeholder/no-call counter hash를 묶되 receipt 후에도 execution permission 0, API call 0 | high | invocation receipt 제거, M8ZR 유지 |
| M8ZT | M8ZS | disabled first-call post-invocation audit | invocation receipt/claim-boundary/no-call counter hash를 묶되 audit 후에도 execution permission 0, API call 0 | high | post-invocation audit 제거, M8ZS 유지 |
| M8ZU | M8ZT | disabled first-call completion summary | post-invocation audit/claim-boundary/no-call counter hash를 묶되 summary 후에도 execution permission 0, API call 0 | high | completion summary 제거, M8ZT 유지 |
| M8ZV | M8ZU | disabled first-call closeout record | completion summary/claim-boundary/no-call counter hash를 묶되 closeout 후에도 execution permission 0, API call 0 | high | closeout record 제거, M8ZU 유지 |
| M8ZW | M8ZV | disabled first-call operator handback | closeout/operator-review/claim-boundary/no-call counter hash를 묶되 handback 후에도 execution permission 0, API call 0 | high | operator handback 제거, M8ZV 유지 |
| M8ZX | M8ZW | disabled first-call operator decision packet | handback/operator-decision/claim-boundary/no-call counter hash를 묶되 decision packet 후에도 execution permission 0, API call 0 | high | operator decision packet 제거, M8ZW 유지 |
| M8ZY | M8ZX | disabled first-call operator release attestation | decision packet/operator-attestation/claim-boundary/no-call counter hash를 묶되 attestation 후에도 execution permission 0, API call 0 | high | operator release attestation 제거, M8ZX 유지 |
| M8ZZ | M8ZY | disabled first-call release authorization seal | release attestation/seal-material/claim-boundary/no-call counter hash를 묶되 seal 후에도 execution permission 0, API call 0 | high | release authorization seal 제거, M8ZY 유지 |
| M8ZZA | M8ZZ | disabled first-call execution authorization capsule | release seal/final authorization/claim-boundary/no-call counter hash를 묶되 capsule 후에도 execution permission 0, API call 0 | high | execution authorization capsule 제거, M8ZZ 유지 |
| M8ZZB | M8ZZA | disabled first-call execution capsule export/read-model | execution capsule/export metadata/claim-boundary/no-call counter hash를 묶되 export 후에도 execution permission 0, API call 0 | high | execution capsule export/read-model 제거, M8ZZA 유지 |
| M8ZZC | M8ZZB | disabled first-call execution capsule handoff packet | execution capsule export/read-model/claim-boundary/no-call counter hash를 묶되 handoff 후에도 execution permission 0, API call 0 | high | execution capsule handoff packet 제거, M8ZZB 유지 |
| M8ZZD | M8ZZC | disabled first-call execution capsule operator review | execution capsule handoff packet/operator-review/claim-boundary/no-call counter hash를 묶되 review 후에도 execution permission 0, API call 0 | high | execution capsule operator review 제거, M8ZZC 유지 |
| M8ZZE | M8ZZD | disabled first-call execution capsule operator decision | execution capsule operator review/operator-decision/claim-boundary/no-call counter hash를 묶되 decision 후에도 execution permission 0, API call 0 | high | execution capsule operator decision 제거, M8ZZD 유지 |
| M8ZZF | M8ZZE | disabled first-call execution capsule release attestation | execution capsule operator decision/release-attestation/claim-boundary/no-call counter hash를 묶되 attestation 후에도 execution permission 0, API call 0 | high | execution capsule release attestation 제거, M8ZZE 유지 |
| M8ZZG | M8ZZF | disabled first-call execution capsule release seal | execution capsule release attestation/seal-material/claim-boundary/no-call counter hash를 묶되 seal 후에도 execution permission 0, API call 0 | high | execution capsule release seal 제거, M8ZZF 유지 |
| M8ZZH | M8ZZG | disabled first-call execution capsule final authorization | execution capsule release seal/final-authorization/claim-boundary/no-call counter hash를 묶되 authorization 후에도 execution permission 0, API call 0 | high | execution capsule final authorization 제거, M8ZZG 유지 |
| M8ZZI | M8ZZH | disabled first-call execution capsule authorization export/read-model | execution capsule final authz/export metadata/claim-boundary/no-call counter hash를 묶되 export 후에도 execution permission 0, API call 0 | high | execution capsule authorization export/read-model 제거, M8ZZH 유지 |
| M8ZZJ | M8ZZI | disabled first-call execution capsule authorization handoff packet | execution capsule authz export/read-model/claim-boundary/no-call counter hash를 묶되 handoff 후에도 execution permission 0, API call 0 | high | execution capsule authorization handoff packet 제거, M8ZZI 유지 |
| M8ZZK | M8ZZJ | disabled first-call execution capsule authorization operator review | execution capsule authz handoff packet/operator-review/claim-boundary/no-call counter hash를 묶되 review 후에도 execution permission 0, API call 0 | high | execution capsule authorization operator review 제거, M8ZZJ 유지 |
| M8ZZL | M8ZZK | disabled first-call execution capsule authorization operator decision | execution capsule authz operator-review/operator-decision/claim-boundary/no-call counter hash를 묶되 decision 후에도 execution permission 0, API call 0 | high | execution capsule authorization operator decision 제거, M8ZZK 유지 |
| M8ZZM | M8ZZL | disabled first-call execution capsule authorization release attestation | execution capsule authz operator-decision/release-attestation/claim-boundary/no-call counter hash를 묶되 attestation 후에도 execution permission 0, API call 0 | high | execution capsule authorization release attestation 제거, M8ZZL 유지 |
| M8ZZN | M8ZZM | disabled first-call execution capsule authorization release seal | execution capsule authz release-attestation/seal-material/claim-boundary/no-call counter hash를 묶되 seal 후에도 execution permission 0, API call 0 | high | execution capsule authorization release seal 제거, M8ZZM 유지 |
| M8ZZO | M8ZZN | disabled first-call execution capsule authorization final authorization | execution capsule authz release seal/final-authorization/claim-boundary/no-call counter hash를 묶되 authorization 후에도 execution permission 0, API call 0 | high | execution capsule authorization final authorization 제거, M8ZZN 유지 |
| M8ZZP | M8ZZO | disabled first-call execution capsule authorization final authorization export/read-model | execution capsule authz final authorization/export metadata/claim-boundary/no-call counter hash를 묶되 export 후에도 execution permission 0, API call 0 | high | execution capsule authorization final authorization export/read-model 제거, M8ZZO 유지 |
| M8ZZQ | M8ZZP | disabled first-call execution capsule authorization final authorization handoff packet | execution capsule authz final authorization export/read-model/claim-boundary/no-call counter hash를 묶되 handoff 후에도 execution permission 0, API call 0 | high | execution capsule authorization final authorization handoff packet 제거, M8ZZP 유지 |
| M8ZZR | M8ZZQ | disabled first-call execution capsule authorization final authorization operator review | execution capsule authz final authorization handoff/operator-review/claim-boundary/no-call counter hash를 묶되 review 후에도 execution permission 0, API call 0 | high | execution capsule authorization final authorization operator review 제거, M8ZZQ 유지 |
| M8ZZS | M8ZZR | disabled first-call execution capsule authorization final authorization operator decision | execution capsule authz final authorization operator-review/operator-decision/claim-boundary/no-call counter hash를 묶되 decision 후에도 execution permission 0, API call 0 | high | execution capsule authorization final authorization operator decision 제거, M8ZZR 유지 |
| M9 | M7,M8T,M8U,M8V,M8W,M8X,M8Y,M8Z,M8ZA,M8ZB,M8ZC,M8ZD,M8ZE,M8ZF,M8ZG,M8ZH,M8ZI,M8ZJ,M8ZK,M8ZL,M8ZM,M8ZN,M8ZO,M8ZP,M8ZQ,M8ZR,M8ZS,M8ZT,M8ZU,M8ZV,M8ZW,M8ZX,M8ZY,M8ZZ,M8ZZA,M8ZZB,M8ZZC,M8ZZD,M8ZZE,M8ZZF,M8ZZG,M8ZZH,M8ZZI,M8ZZJ,M8ZZK,M8ZZL,M8ZZM,M8ZZN,M8ZZO,M8ZZP,M8ZZQ,M8ZZR | 실제 end-to-end demo | live-open 조건을 만족한 샘플 1개가 검증 리포트까지 생성 | high | demo claim 축소 |

Status note: M4 is implemented as an offline contract adapter. M8 has an offline runner boundary, a provider-boundary design, an AW-NEXT-06 `RunnerProviderRegistry` skeleton, an AW-NEXT-07A PRD/ImplementationBrief approval gate, an AW-NEXT-07B side-effect-free dry-run runner, an AW-NEXT-08 gated fake live runner skeleton, an AW-NEXT-09 fake Solar Pro 3 provider boundary skeleton, an AW-NEXT-10 structural approval signature/nonce replay gate, an AW-NEXT-11 verifier/replay store skeleton, an AW-NEXT-12 verifier policy/key identity skeleton, an AW-NEXT-13 resolver/registry/durable replay boundary skeleton, an AW-PERSIST-02 approval/replay repository boundary skeleton with local file-backed replay fixtures, an AW-PERSIST-06 optional SQLite-backed replay wiring path for fake admission, an AW-PERSIST-07 canonical approval persistence service before replay claim, an AW-API-01 sanitized fake admission API demo path, AW-API-02 SQLite-backed fake admission API wiring, AW-API-03 sanitized evidence read-model API skeleton, AW-API-04 optional fixture evidence persistence, AW-API-05 repository-backed run/artifact read API skeleton, AW-PERSIST-08 SQLite-backed canonical run/artifact repository skeleton, AW-API-06 canonical run/evidence composed read model, AW-DEMO-01 local service-shaped demo, AW-DEMO-02 minimal run status surface, AW-LIVE-00 fail-closed live-open policy gate, AW-DEMO-03 static UI shell, AW-LIVE-01 disabled Solar Pro 3 provider adapter skeleton, AW-LIVE-02 no-call Solar Pro 3 contract fixtures, AW-LIVE-03 provider envelope persistence/read-model projection, AW-LIVE-04 provider envelope admission service, AW-LIVE-05 provider envelope API/read-model hook, AW-LIVE-06 operator approval envelope, AW-LIVE-07 dry-admission checklist/runbook projection, AW-LIVE-08 manual provider test proposal gate, AW-LIVE-09 disabled manual provider test executor boundary, AW-LIVE-10 blocked one-shot permission contract projection, AW-LIVE-11 blocked manual provider test preflight audit bundle, AW-LIVE-12 blocked readiness decision record, AW-LIVE-13 blocked review packet, AW-LIVE-14 hash-only review packet export/read-model, AW-LIVE-15 final no-call handoff packet, AW-LIVE-16 first live-call operator opt-in checklist boundary, AW-LIVE-17 sealed pre-execution packet boundary, AW-LIVE-18 no-call live execution arming record, AW-LIVE-19 no-call execution authorization release proposal, AW-LIVE-20 no-call final release packet, AW-LIVE-21 disabled first-call execution switch, AW-LIVE-22 disabled first-call executor preflight, AW-LIVE-23 disabled first-call executor dispatch record, AW-LIVE-24 disabled first-call invocation receipt, AW-LIVE-25 disabled first-call post-invocation audit, AW-LIVE-26 disabled first-call completion summary, AW-LIVE-27 disabled first-call closeout record, AW-LIVE-28 disabled first-call operator handback, AW-LIVE-29 disabled first-call operator decision packet, AW-LIVE-30 disabled first-call operator release attestation, AW-LIVE-31 disabled first-call release authorization seal, AW-LIVE-32 disabled first-call execution authorization capsule, AW-LIVE-33 disabled first-call execution capsule export/read-model, AW-LIVE-34 disabled first-call execution capsule handoff packet, AW-LIVE-35 disabled first-call execution capsule operator review, AW-LIVE-36 disabled first-call execution capsule operator decision, AW-LIVE-37 disabled first-call execution capsule release attestation, AW-LIVE-38 disabled first-call execution capsule release seal, AW-LIVE-39 disabled first-call execution capsule final authorization, AW-LIVE-40 disabled first-call execution capsule authorization export/read-model, AW-LIVE-41 disabled first-call execution capsule authorization handoff packet, AW-LIVE-42 disabled first-call execution capsule authorization operator review, AW-LIVE-43 disabled first-call execution capsule authorization operator decision, AW-LIVE-44 disabled first-call execution capsule authorization release attestation, AW-LIVE-45 disabled first-call execution capsule authorization release seal, AW-LIVE-46 disabled first-call execution capsule authorization final authorization, AW-LIVE-47 disabled first-call execution capsule authorization final authorization export/read-model, AW-LIVE-48 disabled first-call execution capsule authorization final authorization handoff packet, AW-LIVE-49 disabled first-call execution capsule authorization final authorization operator review, and AW-LIVE-50 disabled first-call execution capsule authorization final authorization operator decision. Offline, dry-run, and fake live are registered by default. Live DAACS extraction, production-grade DB persistence, production approval signing, production key registry, multi-host replay prevention, Solar Pro 3 calls, and target runtime calls are still not implemented.

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
