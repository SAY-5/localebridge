"""FastAPI app exposing the review queue and translation lookup."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .tm import InMemoryTM
from .validators import (
    validate_icu,
    validate_length,
    validate_plural_coverage,
    validate_unicode,
)


class ReviewBody(BaseModel):
    action: str  # approve | edit | reject
    edited_text: str | None = None
    reason: str | None = None


def _warnings_for(key: str, locale: str, source_text: str, translated_text: str) -> list[dict[str, str]]:
    issues = []
    issues.extend(validate_icu(key, locale, translated_text))
    issues.extend(validate_unicode(key, locale, translated_text))
    issues.extend(validate_plural_coverage(key, locale, source_text, translated_text))
    issues.extend(validate_length(key, locale, source_text, translated_text))
    return [{"code": i.code, "severity": i.severity, "message": i.message} for i in issues]


def create_app(tm: InMemoryTM | None = None) -> FastAPI:
    tm = tm or InMemoryTM()
    app = FastAPI(title="LocaleBridge", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/translations/{locale}")
    def list_for_locale(locale: str) -> list[dict[str, Any]]:
        return [t.model_dump() for t in tm.all_for_locale(locale)]

    @app.get("/v1/queue")
    def pending_queue() -> list[dict[str, Any]]:
        """Diff-and-approve queue: every pending item with its source,
        AI translation, and the validator warnings a reviewer should see."""
        out: list[dict[str, Any]] = []
        for t in tm.pending():
            out.append(
                {
                    "key": t.key,
                    "locale": t.locale,
                    "source": t.source_text,
                    "ai_translation": t.translated_text,
                    "validator_warnings": _warnings_for(
                        t.key, t.locale, t.source_text, t.translated_text
                    ),
                }
            )
        return out

    @app.post("/v1/translations/{locale}/{key}/review")
    def review(locale: str, key: str, body: ReviewBody) -> dict[str, Any]:
        existing = tm.get(key, locale)
        if existing is None:
            raise HTTPException(status_code=404, detail="translation not found")
        if body.action == "approve":
            existing.status = "approved"
        elif body.action == "edit":
            if body.edited_text is None:
                raise HTTPException(status_code=400, detail="edited_text required")
            existing.translated_text = body.edited_text
            existing.status = "edited"
            existing.edit_reason = body.reason
        elif body.action == "reject":
            existing.status = "rejected"
            existing.reject_reason = body.reason
        else:
            raise HTTPException(status_code=400, detail=f"unknown action {body.action!r}")
        tm.put(existing)
        return existing.model_dump()

    app.state.tm = tm
    return app


def serve() -> None:  # pragma: no cover - thin wrapper for `localebridge-serve`
    import uvicorn

    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
