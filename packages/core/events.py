"""Event stream contracts for workflow observability."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .schemas import WorkflowStage, utc_now
from .security import redact_secrets


@dataclass(slots=True)
class WorkflowEvent:
    """Single observable event emitted by a planner, builder, or verifier."""

    run_id: str
    stage: WorkflowStage
    source: str
    message: str
    level: str = "info"
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["stage"] = self.stage.value
        data["message"] = redact_secrets(data["message"])
        data["payload"] = redact_secrets(data["payload"])
        return data

