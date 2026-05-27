"""Adapters from DIV-style state into workbench contracts."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from packages.core.evidence import sanitize_evidence
from packages.core.schemas import BuildSpec, PlanningBlueprint, PRDPackage


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, dict):
        return [value]
    return [value]


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        return dumped if isinstance(dumped, dict) else {}
    if hasattr(value, "dict"):
        dumped = value.dict()
        return dumped if isinstance(dumped, dict) else {}
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    return {}


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text or default


def _first_text(*values: Any, default: str = "") -> str:
    for value in values:
        if isinstance(value, list | tuple):
            for item in value:
                text = _text(item)
                if text:
                    return text
        else:
            text = _text(value)
            if text:
                return text
    return default


def _section_title(section: Any) -> str:
    section_dict = _as_dict(section)
    if section_dict:
        title = _first_text(section_dict.get("title"), section_dict.get("section_title"))
        number = _text(section_dict.get("section_number"))
        if title and number and not title.startswith(f"{number}."):
            return f"{number}. {title}"
        return title
    return _text(section)


def _section_content(section: Any) -> str:
    section_dict = _as_dict(section)
    if section_dict:
        return _first_text(section_dict.get("content"), section_dict.get("body"), section_dict.get("markdown"))
    return _text(section)


def _normalize_blueprint_items(blueprint: Any) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for item in _as_list(blueprint):
        item_dict = _as_dict(item)
        if item_dict:
            items.append(item_dict)
    return items


def _normalize_sections(sections: Any) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for section in _as_list(sections):
        section_dict = _as_dict(section)
        if section_dict:
            normalized.append(section_dict)
        elif _text(section):
            normalized.append({"title": _text(section)[:80], "content": _text(section)})
    return normalized


def _normalize_evidence_item(item: Any, *, fallback_title: str = "DIV evidence") -> dict[str, Any] | None:
    item_dict = _as_dict(item)
    if item_dict:
        return {
            "title": item_dict.get("title") or item_dict.get("query") or item_dict.get("item_type") or fallback_title,
            "url": item_dict.get("url") or "",
            "summary": item_dict.get("summary") or item_dict.get("snippet") or item_dict.get("content") or item_dict.get("analysis_result") or "",
            "score": item_dict.get("score"),
        }
    text = _text(item)
    if not text:
        return None
    return {"title": fallback_title, "url": "", "summary": text}


def _extract_evidence(research: dict[str, Any], sections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw_items: list[dict[str, Any]] = []
    evidence_sources = [
        research.get("evidence_store"),
        research.get("gathered_evidence"),
        research.get("search_results"),
        research.get("extracted_results"),
    ]
    for source in evidence_sources:
        for item in _as_list(source):
            normalized = _normalize_evidence_item(item)
            if normalized:
                raw_items.append(normalized)

    analysis_result = _text(research.get("analysis_result"))
    if analysis_result:
        raw_items.append({"title": "DIV research analysis", "url": "", "summary": analysis_result})

    for section in sections:
        title = _first_text(section.get("title"), section.get("section_title"), default="Section evidence")
        for evidence in _as_list(section.get("evidence")):
            normalized = _normalize_evidence_item(evidence, fallback_title=title)
            if normalized:
                raw_items.append(normalized)

    return sanitize_evidence(raw_items)


def _extract_visual_artifacts(plan: dict[str, Any], visual: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = _as_visual_artifact_list(plan.get("visual_artifacts")) + _as_visual_artifact_list(
        visual.get("artifacts")
    )
    artifacts: list[dict[str, Any]] = []
    for item in candidates:
        item_dict = _as_dict(item)
        if item_dict:
            artifacts.append(item_dict)
    return artifacts


def _as_visual_artifact_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list | tuple):
        return list(value)
    if isinstance(value, dict):
        if not value:
            return []
        if "section_number" in value or "meta" in value:
            return [value]
        return list(value.values())
    return [value]


def _extract_markdown(plan: dict[str, Any], sections: list[dict[str, Any]]) -> str:
    markdown = _text(plan.get("final_markdown"))
    if markdown:
        return markdown
    rendered_sections: list[str] = []
    for section in sections:
        title = _section_title(section)
        content = _section_content(section)
        if title and content:
            rendered_sections.append(f"## {title}\n\n{content}")
        elif content:
            rendered_sections.append(content)
    return "\n\n".join(rendered_sections)


def planning_blueprint_from_div_state(state: dict[str, Any]) -> PlanningBlueprint:
    """Convert a DIV GlobalState-like dict into a PlanningBlueprint.

    This adapter intentionally accepts plain dictionaries so the first migration
    can wrap existing DIV graph outputs without importing Streamlit or binding
    to the original state classes.
    """
    state_dict = _as_dict(state)
    idea = _as_dict(state_dict.get("idea"))
    plan = _as_dict(state_dict.get("plan"))
    research = _as_dict(state_dict.get("research"))
    supervision = _as_dict(state_dict.get("supervision"))
    visual = _as_dict(state_dict.get("visual"))
    sections = _normalize_sections(plan.get("sections"))
    blueprint_items = _normalize_blueprint_items(idea.get("blueprint"))
    toc = [_text(item) for item in _as_list(idea.get("toc")) if _text(item)]

    title = (
        _first_text(
            idea.get("title"),
            idea.get("project_title"),
            plan.get("title"),
            toc[:1],
            default="Agentic Workbench Plan",
        )
    )
    problem = _first_text(
        idea.get("problem"),
        idea.get("summary"),
        idea.get("rationale"),
        plan.get("summary"),
        supervision.get("goal"),
        default="No problem statement provided.",
    )

    features = [
        _first_text(item.get("title"), item.get("section_title"))
        for item in blueprint_items
        if _first_text(item.get("title"), item.get("section_title"))
    ]
    features.extend(_section_title(section) for section in sections if _section_title(section))
    features = list(dict.fromkeys(features))
    if not features:
        features = toc

    explicit_goals = [str(goal) for goal in _as_list(idea.get("goals")) if _text(goal)]
    goals = explicit_goals or [
        goal
        for goal in [
            _text(supervision.get("goal")),
            _text(idea.get("planning_style")),
            _text(idea.get("rationale")),
        ]
        if goal
    ]
    user_flows = [
        _first_text(item.get("title"), item.get("guideline"), item.get("content"))
        for item in blueprint_items
        if item.get("is_required_from_user") is False
    ]

    blueprint = PlanningBlueprint(
        title=str(title),
        problem=str(problem),
        goals=goals,
        user_flows=user_flows or [str(flow) for flow in _as_list(idea.get("user_flows")) if _text(flow)],
        features=features,
        evidence=_extract_evidence(research, sections),
        visual_artifacts=_extract_visual_artifacts(plan, visual),
        markdown=_extract_markdown(plan, sections),
        assumptions=[
            "Converted from DIV state without importing the Streamlit UI layer.",
            "Converted from dict-like GlobalState to avoid DIV import-time Qdrant/Tavily side effects.",
            "Research evidence is optional and may be empty in offline runs.",
        ],
    )
    blueprint.validate()
    return blueprint


def _requirement_lines(values: list[Any], *, fallback: str) -> list[str]:
    lines = [_text(value) for value in values if _text(value)]
    return lines or [fallback]


def _api_requirements(build_spec: BuildSpec | None) -> list[dict[str, Any]]:
    if build_spec is None:
        return []
    requirements: list[dict[str, Any]] = []
    for endpoint in build_spec.api_spec.get("endpoints", []):
        if not isinstance(endpoint, dict):
            continue
        requirements.append(
            {
                "method": endpoint.get("method", "GET"),
                "path": endpoint.get("path", ""),
                "description": endpoint.get("description", ""),
            }
        )
    return requirements


def _data_entities(build_spec: BuildSpec | None) -> list[dict[str, Any]]:
    if build_spec is None:
        return []
    entities: list[dict[str, Any]] = []
    for model in build_spec.api_spec.get("data_models", []):
        if not isinstance(model, dict):
            continue
        entities.append(
            {
                "name": model.get("name", "Entity"),
                "source_feature": model.get("source_feature", ""),
                "fields": model.get("fields", {}),
            }
        )
    return entities


def _visual_requirements(blueprint: PlanningBlueprint) -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = []
    for artifact in blueprint.visual_artifacts:
        item = _as_dict(artifact)
        meta = _as_dict(item.get("meta"))
        if not item and not meta:
            continue
        requirements.append(
            {
                "section_number": item.get("section_number"),
                "visual_type": meta.get("visual_type") or item.get("visual_type"),
                "purpose": meta.get("purpose") or item.get("purpose"),
            }
        )
    return requirements


def _evidence_summary(blueprint: PlanningBlueprint) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for item in blueprint.evidence[:5]:
        evidence = _as_dict(item)
        summary.append(
            {
                "title": evidence.get("title", "Evidence"),
                "url": evidence.get("url", ""),
                "snippet": evidence.get("snippet") or evidence.get("summary", ""),
            }
        )
    return summary


def _prd_markdown(
    blueprint: PlanningBlueprint,
    feature_requirements: list[str],
    acceptance_criteria: list[str],
) -> str:
    feature_block = "\n".join(f"- {feature}" for feature in feature_requirements)
    flow_block = "\n".join(f"- {flow}" for flow in blueprint.user_flows) or "- User flow not specified."
    criteria_block = "\n".join(f"- {criterion}" for criterion in acceptance_criteria)
    evidence_block = "\n".join(
        f"- {item.get('title', 'Evidence')}: {item.get('snippet') or item.get('url', '')}"
        for item in _evidence_summary(blueprint)
    )
    sections = [
        f"# {blueprint.title}",
        f"## Problem\n\n{blueprint.problem}",
        f"## Goals\n\n" + ("\n".join(f"- {goal}" for goal in blueprint.goals) or "- Goal not specified."),
        f"## User Flows\n\n{flow_block}",
        f"## Feature Requirements\n\n{feature_block}",
        f"## Acceptance Criteria\n\n{criteria_block}",
    ]
    if evidence_block:
        sections.append(f"## Evidence Summary\n\n{evidence_block}")
    if blueprint.markdown:
        sections.append(f"## DIV Planning Notes\n\n{blueprint.markdown}")
    return "\n\n".join(sections)


def planning_to_prd_package(
    blueprint: PlanningBlueprint,
    *,
    build_spec: BuildSpec | None = None,
) -> PRDPackage:
    """Create a human-reviewable PRD package from a planning blueprint."""
    blueprint.validate()
    if build_spec is not None:
        build_spec.validate()

    feature_requirements = _requirement_lines(
        blueprint.features,
        fallback="Define a minimal usable workflow from the approved idea.",
    )
    acceptance_criteria = (
        list(build_spec.acceptance_criteria)
        if build_spec is not None
        else [f"Feature requirement is addressed: {feature}" for feature in feature_requirements]
    )
    test_scenarios = [f"Verify acceptance criterion: {criterion}" for criterion in acceptance_criteria]
    priorities = [
        {"rank": index + 1, "feature": feature, "priority": "must"}
        for index, feature in enumerate(feature_requirements)
    ]

    package = PRDPackage(
        product_name=blueprint.title,
        problem=blueprint.problem,
        prd_markdown=_prd_markdown(blueprint, feature_requirements, acceptance_criteria),
        feature_requirements=feature_requirements,
        user_flows=_requirement_lines(blueprint.user_flows, fallback="User submits idea and reviews output."),
        api_requirements=_api_requirements(build_spec),
        data_entities=_data_entities(build_spec),
        visual_requirements=_visual_requirements(blueprint),
        acceptance_criteria=acceptance_criteria,
        test_scenarios=test_scenarios,
        priorities=priorities,
        evidence_summary=_evidence_summary(blueprint),
        source_blueprint_title=blueprint.title,
    )
    package.validate()
    return package
