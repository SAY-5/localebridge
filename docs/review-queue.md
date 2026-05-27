# Human review queue

Translations can pass through a human before they reach the locale files. The
orchestrator exposes a small review API and `apps/review-ui` is a React
diff-and-approve client for it.

## Pipeline review mode

`run(..., review_mode=True)` enters every freshly translated string into the
translation memory as `pending_review` instead of auto-approving it. The
translation-memory recall rules then decide what happens on the next run:

| Cached status | Next run |
|---------------|----------|
| `pending_review` | reused as-is (still waiting) |
| `approved` | reused, never re-translated |
| `edited` | reused verbatim, never re-translated |
| `rejected` | re-translated, reject reason passed back as `note` |
| (absent) | translated fresh |

This is the "TM remembers" guarantee: an edit survives across runs without a
second LLM call.

## API

- `GET /v1/queue` lists pending items as `{key, locale, source, ai_translation, validator_warnings}`.
- `POST /v1/translations/{locale}/{key}/review` with one of:
  - `{"action": "approve"}`
  - `{"action": "edit", "edited_text": "...", "reason": "..."}`
  - `{"action": "reject", "reason": "..."}`

Approved and edited entries are written to the locale JSON on the next run;
rejected entries are skipped by the writer and re-translated.

## UI

`apps/review-ui` renders each pending item as a card showing the source, the AI
translation, validator warnings, and an editable field with a word-level diff
against the AI output. RTL locales (ar) render with `dir="rtl"`. Approve is
disabled while there are validation errors or an unsaved edit; Save edit is
enabled only once the text differs.

```bash
pnpm --filter ./apps/review-ui typecheck
pnpm --filter ./apps/review-ui test
```
