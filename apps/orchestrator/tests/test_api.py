"""FastAPI review-endpoint tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from localebridge.api import create_app
from localebridge.models import Translation
from localebridge.tm import InMemoryTM


def _seeded_tm() -> InMemoryTM:
    tm = InMemoryTM()
    tm.put(
        Translation(
            key="nav.home",
            locale="es",
            source_text="Home",
            translated_text="Inicio",
            status="pending_review",
        )
    )
    return tm


def test_health() -> None:
    client = TestClient(create_app())
    assert client.get("/health").json() == {"status": "ok"}


def test_approve_flow() -> None:
    tm = _seeded_tm()
    client = TestClient(create_app(tm))
    r = client.post("/v1/translations/es/nav.home/review", json={"action": "approve"})
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "approved"


def test_edit_flow_stores_edit_reason() -> None:
    tm = _seeded_tm()
    client = TestClient(create_app(tm))
    r = client.post(
        "/v1/translations/es/nav.home/review",
        json={"action": "edit", "edited_text": "Página principal", "reason": "more natural"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["translated_text"] == "Página principal"
    assert body["status"] == "edited"
    assert body["edit_reason"] == "more natural"


def test_review_missing_translation_404() -> None:
    client = TestClient(create_app(InMemoryTM()))
    r = client.post("/v1/translations/es/nope/review", json={"action": "approve"})
    assert r.status_code == 404
