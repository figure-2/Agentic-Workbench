from packages.core.events import WorkflowEvent
from packages.core.schemas import WorkflowStage
from packages.core.security import redact_secrets


def test_redact_secret_like_values_in_text():
    text = "OPENAI_API_KEY=sk-abc123456789012345"
    assert "[REDACTED_SECRET]" in redact_secrets(text)


def test_event_redacts_payload_and_message():
    event = WorkflowEvent(
        run_id="run-test",
        stage=WorkflowStage.BUILD,
        source="test",
        message="token=xoxb-secret-token",
        payload={"password": "password=supersecret"},
    )
    data = event.to_dict()
    assert data["message"] == "[REDACTED_SECRET]"
    assert data["payload"]["password"] == "[REDACTED_SECRET]"


def test_redacts_secret_pii_db_url_bearer_token_and_paths():
    payload = {
        "authorization": "Bearer live-secret-token",
        "database": "postgres://user:password@example.com:5432/app",
        "contact": "owner@example.com / 010-1234-5678",
        "windows_path": r"F:\File\02_Project\.env",
        "linux_path": "/home/user/project/.env",
    }

    redacted = redact_secrets(payload)

    assert redacted["authorization"] == "[REDACTED_SECRET]"
    assert redacted["database"] == "[REDACTED_SECRET]"
    assert redacted["contact"] == "[REDACTED_PII] / [REDACTED_PII]"
    assert redacted["windows_path"] == "[REDACTED_PATH]"
    assert redacted["linux_path"] == "[REDACTED_PATH]"


def test_redacts_nested_sensitive_keys_recursively():
    payload = {
        "outer": [
            {"cookie": "session=abc"},
            ("email me at user@example.com", {"raw_content": "full private search result"}),
        ]
    }

    redacted = redact_secrets(payload)

    assert redacted["outer"][0]["cookie"] == "[REDACTED_SECRET]"
    assert redacted["outer"][1][0] == "email me at [REDACTED_PII]"
    assert redacted["outer"][1][1]["raw_content"] == "[REDACTED_SECRET]"
