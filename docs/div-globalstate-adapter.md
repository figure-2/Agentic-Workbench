# DIV GlobalState Adapter

## Conclusion

`DIV GlobalState -> PlanningBlueprint` adapter is an offline contract adapter. It does not import DIV runtime modules, Streamlit, LangChain, Tavily, Qdrant, or Upstage clients.

## Source Shape

| DIV GlobalState field | Meaning | Workbench mapping |
|---|---|---|
| `idea.blueprint[]` | DIV's primary planning blueprint items | `features`, `user_flows` |
| `idea.planning_style` | planning style selected by idea agent | `goals` |
| `idea.rationale` | reason/problem framing | `problem`, `goals` |
| `idea.toc[]` | document outline | `title`, fallback `features` |
| `plan.sections[]` | generated plan sections | `features`, `markdown`, section evidence |
| `plan.final_markdown` | final planning document | `markdown` |
| `plan.visual_artifacts` | generated tables/diagrams/charts | `visual_artifacts` |
| `visual.artifacts` | secondary visual artifact map | `visual_artifacts` |
| `research.evidence_store` | collected evidence | sanitized `evidence` |
| `research.gathered_evidence` | legacy evidence alias | sanitized `evidence` |
| `research.search_results` | search result objects | sanitized `evidence` |
| `research.analysis_result` | research summary or error text | sanitized `evidence` |

## Contract Rules

- Accept dict-like state only; do not import original DIV classes.
- Treat `idea.blueprint` as the primary source of planning intent.
- Treat `plan.sections` as generated execution output that can enrich the blueprint.
- Convert string evidence into public evidence snippets instead of dropping it.
- Sanitize evidence through the shared evidence boundary.
- Preserve visual artifacts when they are structured dicts.
- Ignore empty `visual_artifacts={}` from the Streamlit initial state.
- Keep fallback behavior explicit for malformed or partial state.

## Side-Effect Boundary

Original DIV `research.py` initializes Qdrant and provider/search dependencies at import time. The adapter therefore reads only plain state payloads and must keep live import/API calls at zero.

## Known Limits

- This adapter does not execute DIV graphs.
- It does not measure Solar Pro 3 or any live model output.
- It does not validate generated planning quality.
- It normalizes inconsistent state shapes but does not repair semantically wrong upstream content.

