import { ApiError, apiJson } from "@/lib/api/client";
import type { RetrieveVerseCard } from "@/types/guidance";

/** Ordered citation keys from SQLite (full corpus for Learn deck). */
export async function fetchCitationIndex(signal?: AbortSignal): Promise<string[]> {
  const raw = await apiJson<{ citation_keys: string[] }>("/api/v1/verses/citation-index", {
    method: "GET",
    signal,
  });
  return Array.isArray(raw.citation_keys) ? raw.citation_keys : [];
}

export async function fetchVerseCardByKey(
  citationKey: string,
  signal?: AbortSignal,
): Promise<RetrieveVerseCard> {
  const path = `/api/v1/verses/by-key/${encodeURIComponent(citationKey)}`;
  return apiJson<RetrieveVerseCard>(path, { method: "GET", signal });
}

const _BATCH_MAX = 64;

export async function fetchVerseCardsByKeys(
  citationKeys: readonly string[],
  signal?: AbortSignal,
): Promise<Record<string, RetrieveVerseCard>> {
  if (citationKeys.length === 0) return {};
  const out: Record<string, RetrieveVerseCard> = {};
  for (let i = 0; i < citationKeys.length; i += _BATCH_MAX) {
    const slice = citationKeys.slice(i, i + _BATCH_MAX);
    const raw = await apiJson<{ verses: Record<string, RetrieveVerseCard> }>("/api/v1/verses/by-keys", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ citation_keys: [...slice] }),
      signal,
    });
    Object.assign(out, raw.verses ?? {});
  }
  return out;
}

export async function fetchVerseCardByKeyOrNull(
  citationKey: string,
  signal?: AbortSignal,
): Promise<RetrieveVerseCard | null> {
  try {
    return await fetchVerseCardByKey(citationKey, signal);
  } catch (e) {
    if (e instanceof ApiError && e.status === 404) return null;
    throw e;
  }
}
