import { useCallback, useEffect, useState } from "react";
import type { QueueItem, ReviewApi } from "./api";
import { ReviewCard } from "./ReviewCard";

interface Props {
  api: ReviewApi;
}

export function App({ api }: Props) {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems(await api.fetchQueue());
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, [api]);

  useEffect(() => {
    void load();
  }, [load]);

  const onResolved = useCallback((key: string, locale: string) => {
    setItems((prev) => prev.filter((it) => !(it.key === key && it.locale === locale)));
  }, []);

  return (
    <main className="app">
      <header className="app__head">
        <h1 className="app__title">Translation review</h1>
        <p className="app__count">
          {loading ? "Loading…" : `${items.length} pending`}
        </p>
        <button type="button" className="btn" onClick={() => void load()} disabled={loading}>
          Refresh
        </button>
      </header>

      {error && <p className="app__error">{error}</p>}

      {!loading && items.length === 0 && !error && (
        <p className="app__empty">Queue is clear. Nothing waiting for review.</p>
      )}

      <section className="app__queue">
        {items.map((item) => (
          <ReviewCard
            key={`${item.locale}:${item.key}`}
            item={item}
            api={api}
            onResolved={onResolved}
          />
        ))}
      </section>
    </main>
  );
}
