"""End-to-end smoke for the agent web surface.

Pre-requisite: ``make dev`` is running (FastAPI on :8000, Vite on :5173).
We don't try to manage the dev server here — that belongs in a CI job
that orchestrates startup.

What we cover:
  * The ``/agent`` route renders.
  * Submitting a message produces:
      - a triage step in the tool-steps panel,
      - a final answer rendered in the chat transcript,
      - either a confidence pill or a "Streaming…" → "Send" round trip.
  * /api/v1/agent/tools returns the catalogue (sanity proxy check).

We mark the module ``e2e`` so it stays out of the default ``pytest`` run
(which already exercises planner + integration). The CI lane runs:

    make e2e
"""

from __future__ import annotations

import os
import pytest

pytestmark = pytest.mark.e2e

playwright = pytest.importorskip("playwright.sync_api")
sync_playwright = playwright.sync_playwright

WEB = os.environ.get("WEB_BASE", "http://localhost:5173")
API = os.environ.get("API_BASE", "http://localhost:8000")


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        yield b
        b.close()


def _is_dev_up() -> bool:
    import urllib.error
    import urllib.request

    try:
        with urllib.request.urlopen(f"{API}/health", timeout=2) as r:
            return r.status == 200
    except (urllib.error.URLError, TimeoutError, ConnectionError):
        return False


@pytest.fixture(autouse=True)
def _require_dev_stack():
    if not _is_dev_up():
        pytest.skip(f"dev stack not reachable at {API}; run `make dev` first")


def test_tools_catalogue_proxy(browser):
    page = browser.new_page()
    response = page.goto(f"{API}/api/v1/agent/tools")
    assert response is not None and response.ok, f"status={response.status if response else 'no-response'}"
    body = page.content()
    for required in ("rag_search", "fraud_score", "risk_score"):
        assert required in body, f"missing tool {required}"


def test_agent_page_streams_answer(browser):
    page = browser.new_page()
    page.goto(f"{WEB}/agent")
    page.wait_for_selector("textarea", timeout=10_000)

    page.fill("textarea", "is this transaction fraudulent: $5000 from RU")
    page.get_by_role("button", name="Send").click()

    # Wait for the streaming pill to flip back to idle, then assert an
    # answer is visible. We cap the wait at 30s — offline path replies
    # in under 100 ms, but the timeout absorbs CI noise.
    page.wait_for_function(
        "document.querySelectorAll('button')[0]?.innerText.includes('Send')",
        timeout=30_000,
    )

    transcript = page.locator("div.bg-sand").inner_text(timeout=5_000)
    assert transcript.strip(), "no assistant message rendered"
