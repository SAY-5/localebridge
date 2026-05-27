import { useMemo, useState } from "react";
import type { QueueItem, ReviewApi } from "./api";
import { diffTokens } from "./diff";

const RTL_LOCALES = new Set(["ar", "fa", "he", "ur"]);

function dirFor(locale: string): "rtl" | "ltr" {
  return RTL_LOCALES.has(locale.split("-")[0]) ? "rtl" : "ltr";
}

interface Props {
  item: QueueItem;
  api: ReviewApi;
  onResolved: (key: string, locale: string) => void;
}

export function ReviewCard({ item, api, onResolved }: Props) {
  const [draft, setDraft] = useState(item.ai_translation);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const edited = draft !== item.ai_translation;
  const diff = useMemo(() => diffTokens(item.ai_translation, draft), [item.ai_translation, draft]);
  const hasErrors = item.validator_warnings.some((w) => w.severity === "error");

  async function send(action: "approve" | "edit" | "reject") {
    setBusy(true);
    setError(null);
    try {
      if (action === "edit") {
        await api.review(item.locale, item.key, { action, edited_text: draft, reason });
      } else if (action === "reject") {
        await api.review(item.locale, item.key, { action, reason });
      } else {
        await api.review(item.locale, item.key, { action });
      }
      onResolved(item.key, item.locale);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="card" aria-busy={busy}>
      <header className="card__head">
        <code className="card__key">{item.key}</code>
        <span className="card__locale">{item.locale}</span>
      </header>

      <div className="card__row">
        <span className="card__label">Source</span>
        <p className="card__source" dir="ltr">
          {item.source}
        </p>
      </div>

      <div className="card__row">
        <span className="card__label">AI translation</span>
        <p className="card__ai" dir={dirFor(item.locale)}>
          {item.ai_translation}
        </p>
      </div>

      {item.validator_warnings.length > 0 && (
        <ul className="card__warnings">
          {item.validator_warnings.map((w, idx) => (
            <li key={idx} className={`warn warn--${w.severity}`}>
              <span className="warn__code">{w.code}</span> {w.message}
            </li>
          ))}
        </ul>
      )}

      <label className="card__row">
        <span className="card__label">Your edit</span>
        <textarea
          className="card__edit"
          dir={dirFor(item.locale)}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          rows={2}
        />
      </label>

      {edited && (
        <p className="card__diff" aria-label="diff against AI translation">
          {diff.map((tok, idx) => (
            <span key={idx} className={`tok tok--${tok.op}`}>
              {tok.text}
            </span>
          ))}
        </p>
      )}

      <label className="card__row">
        <span className="card__label">Reason (for edit / reject)</span>
        <input
          className="card__reason"
          value={reason}
          placeholder="e.g. house style, wrong register"
          onChange={(e) => setReason(e.target.value)}
        />
      </label>

      {error && <p className="card__error">{error}</p>}

      <div className="card__actions">
        <button
          type="button"
          className="btn btn--approve"
          disabled={busy || edited || hasErrors}
          onClick={() => send("approve")}
        >
          Approve
        </button>
        <button
          type="button"
          className="btn btn--edit"
          disabled={busy || !edited}
          onClick={() => send("edit")}
        >
          Save edit
        </button>
        <button
          type="button"
          className="btn btn--reject"
          disabled={busy}
          onClick={() => send("reject")}
        >
          Reject
        </button>
      </div>
    </article>
  );
}
