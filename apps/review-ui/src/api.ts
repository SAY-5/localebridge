// Thin client for the LocaleBridge orchestrator review API.

export interface ValidatorWarning {
  code: string;
  severity: "error" | "warning";
  message: string;
}

export interface QueueItem {
  key: string;
  locale: string;
  source: string;
  ai_translation: string;
  validator_warnings: ValidatorWarning[];
}

export type ReviewAction = "approve" | "edit" | "reject";

export interface ReviewBody {
  action: ReviewAction;
  edited_text?: string;
  reason?: string;
}

export interface ReviewApi {
  fetchQueue(): Promise<QueueItem[]>;
  review(locale: string, key: string, body: ReviewBody): Promise<void>;
}

export function createReviewApi(baseUrl = ""): ReviewApi {
  return {
    async fetchQueue() {
      const res = await fetch(`${baseUrl}/v1/queue`);
      if (!res.ok) throw new Error(`queue fetch failed: ${res.status}`);
      return (await res.json()) as QueueItem[];
    },
    async review(locale, key, body) {
      const res = await fetch(
        `${baseUrl}/v1/translations/${encodeURIComponent(locale)}/${encodeURIComponent(key)}/review`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        },
      );
      if (!res.ok) throw new Error(`review failed: ${res.status}`);
    },
  };
}
