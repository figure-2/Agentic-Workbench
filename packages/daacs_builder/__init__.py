"""DAACS build layer extraction boundary."""

from .adapters import (
    build_spec_to_daacs_initial_state,
    create_spec_approval,
    ensure_implementation_approved,
    implementation_brief_from_prd_package,
    planning_to_build_spec,
)
from .offline_runner import DAACSOfflineRunner, find_blocked_operation_attempts
from .dry_run_runner import DAACSDryRunRunner, DryRunRunnerProvider
from .approval_persistence import (
    CanonicalApprovalPersistenceError,
    CanonicalApprovalPersistenceResult,
    CanonicalApprovalPersistenceService,
)
from .live_runner import FakeLiveRuntime, LiveRunnerProvider
from .solar_live_adapter import (
    DisabledSolarPro3LiveAdapter,
    ProviderAdapterRegistry,
    SolarPro3LiveAdapterConfig,
    default_solar_provider_adapter_registry,
)
from .runner_provider import (
    ApprovalRecord,
    OfflineRunnerProvider,
    RunnerPlan,
    RunnerPolicy,
    RunnerProviderRegistry,
    RunnerRequest,
    RunnerResult,
    default_runner_provider_registry,
)

__all__ = [
    "ApprovalRecord",
    "CanonicalApprovalPersistenceError",
    "CanonicalApprovalPersistenceResult",
    "CanonicalApprovalPersistenceService",
    "DAACSDryRunRunner",
    "DAACSOfflineRunner",
    "DisabledSolarPro3LiveAdapter",
    "DryRunRunnerProvider",
    "FakeLiveRuntime",
    "LiveRunnerProvider",
    "OfflineRunnerProvider",
    "ProviderAdapterRegistry",
    "RunnerPlan",
    "RunnerPolicy",
    "RunnerProviderRegistry",
    "RunnerRequest",
    "RunnerResult",
    "SolarPro3LiveAdapterConfig",
    "build_spec_to_daacs_initial_state",
    "create_spec_approval",
    "default_runner_provider_registry",
    "default_solar_provider_adapter_registry",
    "ensure_implementation_approved",
    "find_blocked_operation_attempts",
    "implementation_brief_from_prd_package",
    "planning_to_build_spec",
]
