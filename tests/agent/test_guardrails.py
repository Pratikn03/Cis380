"""Guardrail tests: PII scrubbing + safety classifier."""

from __future__ import annotations

from app.agent import guardrails


def test_scrub_email():
    out = guardrails.scrub_pii("contact me at alice@example.com tomorrow")
    assert "[REDACTED:EMAIL]" in out.text
    assert out.counts["email"] == 1


def test_scrub_ssn_cc_phone_ip():
    text = (
        "ssn 123-45-6789, cc 4111-1111-1111-1111, "
        "phone (415) 555-0100, server 192.168.1.1"
    )
    out = guardrails.scrub_pii(text)
    assert "[REDACTED:SSN]" in out.text
    assert "[REDACTED:CC]" in out.text
    assert "[REDACTED:PHONE]" in out.text
    assert "[REDACTED:IP]" in out.text
    assert out.total >= 4


def test_scrub_no_pii_is_idempotent():
    text = "this message has no personal data"
    out = guardrails.scrub_pii(text)
    assert out.text == text
    assert out.total == 0


def test_safety_classifier_offline_allows(monkeypatch):
    """When LLM_MODE=offline the classifier returns allow=True without
    hitting the network."""
    from app.core import settings as settings_mod

    monkeypatch.setattr(settings_mod.agent, "llm_mode", "offline", raising=False)
    verdict = guardrails.classify_output("Some normal answer")
    assert verdict.allow is True
    assert verdict.reason == "offline_mode"


def test_safety_classifier_unavailable_allows(monkeypatch):
    from app.core import settings as settings_mod

    monkeypatch.setattr(settings_mod.agent, "llm_mode", "online", raising=False)

    def _raise():
        raise guardrails.AnthropicUnavailable("no key")

    monkeypatch.setattr(guardrails, "get_anthropic_client", _raise)
    verdict = guardrails.classify_output("anything")
    assert verdict.allow is True
    assert verdict.reason == "classifier_unavailable"
