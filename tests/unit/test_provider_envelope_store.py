import builtins
import json
import os
import socket
import sqlite3
import urllib.request

import pytest

from packages.core.exposure import find_forbidden_public_keys
from packages.core.public_projection import assert_public_projection_safe
from packages.core.schemas import stable_contract_hash
from packages.daacs_builder.provider_boundary import (
    SOLAR_PRO_3_ENV_KEY_NAME,
    SOLAR_PRO_3_MODEL,
    SOLAR_PRO_3_PROVIDER,
    ProviderRequest,
)
from packages.daacs_builder.provider_envelope_store import (
    PROVIDER_ENVELOPE_DB_NAME,
    InMemoryProviderEnvelopeRepository,
    ProviderEnvelopeStoreUnavailableError,
    SQLiteProviderEnvelopeStore,
    provider_envelope_public_read_model,
    provider_envelope_public_read_model_from_sqlite,
    provider_envelope_record_from_contract_result,
    provider_review_packet_export_public_read_model,
    provider_review_packet_export_record_from_projection,
)
from packages.daacs_builder.solar_contracts import (
    SolarCostTimeoutPolicy,
    attach_solar_response_projection_fixture,
    build_solar_request_contract_fixture,
)
from packages.daacs_builder.solar_live_adapter import SOLAR_LIVE_ADAPTER_MODE


def _serialized(value) -> str:
    return json.dumps(value, ensure_ascii=True, sort_keys=True, default=str)


def _prompt_hash() -> str:
    return stable_contract_hash(
        {
            "purpose": "provider envelope persistence fixture",
            "input": "hash only",
        }
    )


def _request(**overrides) -> ProviderRequest:
    fields = {
        "run_id": "run-live-03",
        "prompt_contract_hash": _prompt_hash(),
        "provider_name": SOLAR_PRO_3_PROVIDER,
        "model_name": SOLAR_PRO_3_MODEL,
        "mode": SOLAR_LIVE_ADAPTER_MODE,
        "env_key_name": SOLAR_PRO_3_ENV_KEY_NAME,
        "metadata": {
            "raw_prompt": "LIVE03_RAW_PROMPT_SENTINEL",
            "provider_payload": {"body": "LIVE03_PROVIDER_PAYLOAD_SENTINEL"},
        },
    }
    fields.update(overrides)
    return ProviderRequest(**fields)


def _policy(**overrides) -> SolarCostTimeoutPolicy:
    fields = {
        "request_timeout_seconds": 30,
        "max_cost_units": 1,
        "max_live_api_calls": 1,
        "max_output_tokens": 512,
        "retry_count": 0,
    }
    fields.update(overrides)
    return SolarCostTimeoutPolicy(**fields)


def _contract_result(**request_overrides):
    request_result = build_solar_request_contract_fixture(
        _request(**request_overrides),
        _policy(),
    )
    return attach_solar_response_projection_fixture(
        request_result,
        response_summary="sanitized provider contract projection",
        raw_response_body="LIVE03_PROVIDER_BODY_SENTINEL api_key=secret-value",
    )


def _sqlite_rows(path):
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in connection.execute(
                "SELECT * FROM provider_envelopes ORDER BY created_at ASC, envelope_id ASC"
            )
        ]


def _sqlite_review_packet_rows(path):
    with sqlite3.connect(path) as connection:
        connection.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in connection.execute(
                """
                SELECT * FROM provider_review_packet_exports
                ORDER BY created_at ASC, export_id ASC
                """
            )
        ]


def _review_packet_projection(**overrides):
    fields = {
        "status": "blocked",
        "reason": "review_packet_execution_closed",
        "review_packet_hash": stable_contract_hash(
            {
                "purpose": "provider review packet export",
                "input": "hash only",
            }
        ),
        "component_count": 3,
        "passed_component_count": 3,
        "mismatch_count": 0,
        "component_hash_count": 3,
        "execution_permission_count": 0,
        "raw_prompt": "LIVE14_RAW_PROMPT_SENTINEL",
        "provider_payload": "LIVE14_PROVIDER_PAYLOAD_SENTINEL",
        "authorization_material": "LIVE14_AUTH_SENTINEL",
    }
    fields.update(overrides)
    return fields


def test_provider_envelope_record_persists_request_and_response_contract_hashes():
    result = _contract_result()
    record = provider_envelope_record_from_contract_result(
        result,
        created_at="2026-06-01T00:00:00+00:00",
    )
    repository = InMemoryProviderEnvelopeRepository()

    repository.save(record)
    read_model = provider_envelope_public_read_model(repository, run_id="run-live-03")
    envelope = read_model["provider_envelopes"][0]

    assert read_model["status"] == "available"
    assert read_model["counts"]["provider_envelope_count"] == 1
    assert envelope["request_contract_hash"] == result.request_contract["request_contract_hash"]
    assert envelope["response_contract_hash"] == result.response_projection["response_contract_hash"]
    assert envelope["prompt_contract_hash"] == _prompt_hash()
    assert envelope["status"] == "projected_fixture"
    assert find_forbidden_public_keys(read_model) == []
    assert_public_projection_safe(read_model)


def test_provider_review_packet_export_rows_do_not_store_raw_material(tmp_path):
    store = SQLiteProviderEnvelopeStore(root=tmp_path)
    record = provider_review_packet_export_record_from_projection(
        _review_packet_projection(),
        run_id="run-live-03",
        created_at="2026-06-01T00:00:00+00:00",
    )

    store.repository().save_review_packet_export(record)
    serialized = _serialized(_sqlite_review_packet_rows(store.path))

    for sentinel in (
        "LIVE14_RAW_PROMPT_SENTINEL",
        "LIVE14_PROVIDER_PAYLOAD_SENTINEL",
        "LIVE14_AUTH_SENTINEL",
        "raw_prompt",
        "provider_payload",
        "authorization_material",
    ):
        assert sentinel not in serialized
    assert record.review_packet_hash in serialized
    assert record.content_hash in serialized


def test_provider_review_packet_export_read_model_returns_hash_status_count_only(tmp_path):
    store = SQLiteProviderEnvelopeStore(root=tmp_path)
    record = provider_review_packet_export_record_from_projection(
        _review_packet_projection(),
        run_id="run-live-03",
        created_at="2026-06-01T00:00:00+00:00",
    )
    store.repository().save_review_packet_export(record)

    read_model = provider_review_packet_export_public_read_model(
        store.repository(),
        run_id="run-live-03",
    )
    export = read_model["review_packet_exports"][0]

    assert set(export) == {
        "status",
        "reason",
        "review_packet_hash",
        "review_packet_export_hash",
        "component_count",
        "passed_component_count",
        "mismatch_count",
        "component_hash_count",
        "execution_permission_count",
    }
    assert read_model["status"] == "available"
    assert read_model["counts"]["review_packet_export_count"] == 1
    assert read_model["counts"]["execution_permission_count"] == 0
    assert read_model["repository_boundary"]["raw_row_returned"] is False
    assert read_model["repository_boundary"]["root_path_returned"] is False
    assert read_model["execution_boundary"] == {
        "sdk_imports": 0,
        "env_value_reads": 0,
        "api_calls": 0,
        "network_calls": 0,
    }
    assert_public_projection_safe(read_model)


def test_provider_envelope_sqlite_rows_do_not_store_raw_prompt_or_provider_body(tmp_path):
    result = _contract_result()
    record = provider_envelope_record_from_contract_result(
        result,
        created_at="2026-06-01T00:00:00+00:00",
    )
    store = SQLiteProviderEnvelopeStore(root=tmp_path)

    store.repository().save(record)
    serialized = _serialized(_sqlite_rows(store.path))

    for sentinel in (
        "LIVE03_RAW_PROMPT_SENTINEL",
        "LIVE03_PROVIDER_PAYLOAD_SENTINEL",
        "LIVE03_PROVIDER_BODY_SENTINEL",
        "secret-value",
        "raw_prompt",
        "provider_payload",
        "provider_response",
    ):
        assert sentinel not in serialized
    assert record.request_contract_hash in serialized
    assert record.response_contract_hash in serialized


def test_provider_envelope_public_read_model_returns_hash_count_status_fields_only(tmp_path):
    store = SQLiteProviderEnvelopeStore(root=tmp_path)
    record = provider_envelope_record_from_contract_result(
        _contract_result(),
        created_at="2026-06-01T00:00:00+00:00",
    )
    store.repository().save(record)

    read_model = provider_envelope_public_read_model_from_sqlite(tmp_path, run_id="run-live-03")
    envelope = read_model["provider_envelopes"][0]

    assert set(envelope) == {
        "envelope_id",
        "status",
        "request_contract_hash",
        "response_contract_hash",
        "prompt_contract_hash",
        "content_hash",
        "request_field_count",
        "response_field_count",
        "policy_check_count",
    }
    assert read_model["repository_boundary"]["raw_row_returned"] is False
    assert read_model["repository_boundary"]["root_path_returned"] is False
    assert read_model["execution_boundary"] == {
        "sdk_imports": 0,
        "env_value_reads": 0,
        "api_calls": 0,
        "network_calls": 0,
    }
    assert_public_projection_safe(read_model)


def test_provider_envelope_sqlite_rejects_duplicate_hash_rows(tmp_path):
    store = SQLiteProviderEnvelopeStore(root=tmp_path)
    record = provider_envelope_record_from_contract_result(_contract_result())

    store.repository().save(record)

    with pytest.raises(ValueError, match="duplicate"):
        store.repository().save(record)


def test_provider_envelope_store_blocks_corrupted_or_unavailable_sqlite(tmp_path):
    corrupt_root = tmp_path / "corrupt"
    corrupt_root.mkdir()
    (corrupt_root / PROVIDER_ENVELOPE_DB_NAME).write_text(
        "not a sqlite database",
        encoding="utf-8",
    )

    corrupt_read_model = provider_envelope_public_read_model_from_sqlite(
        corrupt_root,
        run_id="run-live-03",
    )
    assert corrupt_read_model["status"] == "blocked"
    assert corrupt_read_model["counts"]["provider_envelope_count"] == 0
    assert corrupt_read_model["execution_boundary"]["api_calls"] == 0

    unavailable_root = tmp_path / "not-a-directory"
    unavailable_root.write_text("file instead of directory", encoding="utf-8")
    unavailable_read_model = provider_envelope_public_read_model_from_sqlite(
        unavailable_root,
        run_id="run-live-03",
    )
    assert unavailable_read_model["status"] == "blocked"
    assert unavailable_read_model["repository_boundary"]["provider_envelope_store"] == "blocked"

    traversal_read_model = provider_envelope_public_read_model_from_sqlite(
        tmp_path,
        run_id="run-live-03",
        filename="../escaped-provider-envelope.sqlite3",
    )
    assert traversal_read_model["status"] == "blocked"
    assert not (tmp_path.parent / "escaped-provider-envelope.sqlite3").exists()


def test_provider_envelope_store_blocks_wrong_schema_columns(tmp_path):
    db_path = tmp_path / PROVIDER_ENVELOPE_DB_NAME
    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE schema_migrations(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL);
            CREATE TABLE provider_envelopes(
                envelope_id TEXT PRIMARY KEY,
                raw_prompt TEXT NOT NULL
            );
            """
        )

    with pytest.raises(ProviderEnvelopeStoreUnavailableError):
        SQLiteProviderEnvelopeStore(root=tmp_path)

    read_model = provider_envelope_public_read_model_from_sqlite(tmp_path, run_id="run-live-03")
    assert read_model["status"] == "blocked"
    assert find_forbidden_public_keys(read_model) == []


def test_provider_envelope_read_model_blocks_repository_failure():
    class BrokenRepository:
        def save(self, record):
            raise RuntimeError("unavailable")

        def list_for_run(self, run_id):
            raise RuntimeError("unavailable")

    read_model = provider_envelope_public_read_model(BrokenRepository(), run_id="run-live-03")

    assert read_model["status"] == "blocked"
    assert read_model["provider_envelopes"] == []
    assert read_model["execution_boundary"]["network_calls"] == 0
    assert_public_projection_safe(read_model)


def test_provider_envelope_persistence_does_not_read_env_import_sdk_or_call_network(tmp_path, monkeypatch):
    def blocked_getenv(*args, **kwargs):
        raise AssertionError("env value read attempted")

    def blocked_socket(*args, **kwargs):
        raise AssertionError("network socket attempted")

    def blocked_urlopen(*args, **kwargs):
        raise AssertionError("network urlopen attempted")

    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.split(".", 1)[0] in {"upstage", "openai", "requests", "httpx"}:
            raise AssertionError(f"provider SDK import attempted: {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(os, "getenv", blocked_getenv)
    monkeypatch.setattr(socket, "socket", blocked_socket)
    monkeypatch.setattr(urllib.request, "urlopen", blocked_urlopen)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    store = SQLiteProviderEnvelopeStore(root=tmp_path)
    record = provider_envelope_record_from_contract_result(_contract_result())
    store.repository().save(record)
    read_model = provider_envelope_public_read_model_from_sqlite(tmp_path, run_id="run-live-03")

    assert read_model["execution_boundary"] == {
        "sdk_imports": 0,
        "env_value_reads": 0,
        "api_calls": 0,
        "network_calls": 0,
    }
