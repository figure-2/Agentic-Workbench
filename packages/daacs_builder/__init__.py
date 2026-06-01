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
from .solar_contracts import (
    SolarContractFixtureResult,
    SolarCostTimeoutPolicy,
    SolarRequestContractFixture,
    SolarResponseProjectionFixture,
    attach_solar_response_projection_fixture,
    build_solar_request_contract_fixture,
    build_solar_response_projection_fixture,
)
from .provider_envelope_store import (
    InMemoryProviderEnvelopeRepository,
    ProviderEnvelopeRecord,
    ProviderEnvelopeRepository,
    ProviderEnvelopeStoreUnavailableError,
    SQLiteProviderEnvelopeRepository,
    SQLiteProviderEnvelopeStore,
    provider_envelope_public_read_model,
    provider_envelope_public_read_model_from_sqlite,
    provider_envelope_record_from_contract_result,
)
from .provider_envelope_admission import (
    ProviderEnvelopeAdmissionResult,
    ProviderEnvelopeAdmissionService,
    invoke_adapter_after_provider_envelope_admission,
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
    "InMemoryProviderEnvelopeRepository",
    "LiveRunnerProvider",
    "OfflineRunnerProvider",
    "ProviderEnvelopeRecord",
    "ProviderEnvelopeRepository",
    "ProviderEnvelopeAdmissionResult",
    "ProviderEnvelopeAdmissionService",
    "ProviderEnvelopeStoreUnavailableError",
    "ProviderAdapterRegistry",
    "RunnerPlan",
    "RunnerPolicy",
    "RunnerProviderRegistry",
    "RunnerRequest",
    "RunnerResult",
    "SolarContractFixtureResult",
    "SolarCostTimeoutPolicy",
    "SolarPro3LiveAdapterConfig",
    "SolarRequestContractFixture",
    "SolarResponseProjectionFixture",
    "SQLiteProviderEnvelopeRepository",
    "SQLiteProviderEnvelopeStore",
    "attach_solar_response_projection_fixture",
    "build_spec_to_daacs_initial_state",
    "build_solar_request_contract_fixture",
    "build_solar_response_projection_fixture",
    "create_spec_approval",
    "default_runner_provider_registry",
    "default_solar_provider_adapter_registry",
    "ensure_implementation_approved",
    "find_blocked_operation_attempts",
    "implementation_brief_from_prd_package",
    "invoke_adapter_after_provider_envelope_admission",
    "planning_to_build_spec",
    "provider_envelope_public_read_model",
    "provider_envelope_public_read_model_from_sqlite",
    "provider_envelope_record_from_contract_result",
]
