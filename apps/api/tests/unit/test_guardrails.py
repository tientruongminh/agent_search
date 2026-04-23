import pytest

from app.services.page_fetcher import GuardrailViolation, validate_outbound_url


def test_guardrails_block_localhost() -> None:
    with pytest.raises(GuardrailViolation):
        validate_outbound_url("http://127.0.0.1/private")

