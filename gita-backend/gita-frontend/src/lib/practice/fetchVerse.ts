import { fetchVerseCardByKeyOrNull, fetchVerseCardsByKeys } from "@/lib/api/verses";
import type { RetrieveVerseCard } from "@/types/guidance";
import { PRACTICE_DECK_CITATION_KEYS, dayIndexForDate } from "@/lib/practice/dailyDeck";
import { isPlaceholderTranslation } from "@/lib/practice/verseQuality";

/** In-memory (tab session) to avoid duplicate fetches when navigating Today / Learn / Review. */
const _verseHitCache = new Map<string, RetrieveVerseCard>();
const _inFlight = new Map<string, Promise<RetrieveVerseCard | null>>();

const CACHE_MAX = 96;

/** After the first batch prefetch attempt (success or failure); avoids retrying POST on every key. */
let _deckPrefetchDone = false;
let _deckPrefetchPromise: Promise<void> | null = null;

function _cacheRememberHit(citationKey: string, verse: RetrieveVerseCard) {
  _verseHitCache.set(citationKey, verse);
  while (_verseHitCache.size > CACHE_MAX) {
    const first = _verseHitCache.keys().next().value;
    if (first === undefined) break;
    _verseHitCache.delete(first);
  }
}

function _isDeckKey(citationKey: string): boolean {
  return (PRACTICE_DECK_CITATION_KEYS as readonly string[]).includes(citationKey);
}

/**
 * One HTTP round-trip: load every practice-deck verse into the in-memory cache.
 * Safe to call from Today / Learn before walking the deck.
 */
export async function prefetchPracticeDeck(signal?: AbortSignal): Promise<void> {
  if (_deckPrefetchDone) return;
  if (_deckPrefetchPromise) {
    await _deckPrefetchPromise;
    return;
  }
  _deckPrefetchPromise = (async () => {
    const keys = [...PRACTICE_DECK_CITATION_KEYS];
    try {
      const batch = await fetchVerseCardsByKeys(keys, signal);
      for (const k of keys) {
        const v = batch[k];
        if (v && !isPlaceholderTranslation(v.translation)) {
          _cacheRememberHit(k, v);
        }
      }
    } catch {
      /* Batch is optional: proxy down, CORS, or older backend without /verses/by-keys. */
    } finally {
      _deckPrefetchDone = true;
    }
  })();
  try {
    await _deckPrefetchPromise;
  } finally {
    _deckPrefetchPromise = null;
  }
}

/**
 * Best-effort fetch of a single verse card by canonical citation key (e.g. `2.47`).
 * Uses fast DB lookup (`GET /verses/by-key/...`); batch-warms the practice deck when applicable.
 */
export async function fetchVerseByCitationKey(
  citationKey: string,
  signal?: AbortSignal,
): Promise<RetrieveVerseCard | null> {
  const hit = _verseHitCache.get(citationKey);
  if (hit) return hit;

  const existing = _inFlight.get(citationKey);
  if (existing) return existing;

  const p = (async (): Promise<RetrieveVerseCard | null> => {
    if (_isDeckKey(citationKey)) {
      await prefetchPracticeDeck(signal);
      const after = _verseHitCache.get(citationKey);
      if (after) return after;
    }
    const v = await fetchVerseCardByKeyOrNull(citationKey, signal);
    if (!v || isPlaceholderTranslation(v.translation)) {
      return null;
    }
    _cacheRememberHit(citationKey, v);
    return v;
  })();

  _inFlight.set(citationKey, p);
  try {
    return await p;
  } finally {
    _inFlight.delete(citationKey);
  }
}

/**
 * Verse of the Day: walk the practice deck from the calendar slot until a displayable verse loads.
 *
 * Uses one batch request then per-key GET fallbacks — same transport as Learn — and does **not**
 * go through fetchVerseByCitationKey (avoids prefetch + _inFlight interactions that only
 * showed up on Today for some users).
 */
export async function fetchDisplayableVerseForDay(
  d: Date = new Date(),
  signal?: AbortSignal,
): Promise<{ verse: RetrieveVerseCard; citationKey: string } | null> {
  const keys = [...PRACTICE_DECK_CITATION_KEYS];
  const n = keys.length;
  const start = dayIndexForDate(d) % n;
  let batch: Record<string, RetrieveVerseCard> = {};
  try {
    batch = await fetchVerseCardsByKeys(keys, signal);
  } catch {
    /* per-key GET below */
  }
  for (let o = 0; o < n; o++) {
    const k = keys[(start + o) % n]!;
    let card: RetrieveVerseCard | null | undefined = batch[k];
    if (!card || isPlaceholderTranslation(card.translation)) {
      try {
        card = await fetchVerseCardByKeyOrNull(k, signal);
      } catch {
        card = null;
      }
    }
    if (card && !isPlaceholderTranslation(card.translation)) {
      _cacheRememberHit(k, card);
      return { verse: card, citationKey: k };
    }
  }
  return null;
}

/**
 * From a deck index, load the first displayable verse (skips placeholder-only rows).
 * ``deck`` is the ordered citation list (e.g. full DB from ``/verses/citation-index``).
 */
export async function fetchFirstDisplayableInDeckFrom(
  deckIndex: number,
  deck: readonly string[],
  signal?: AbortSignal,
): Promise<{ verse: RetrieveVerseCard; citationKey: string; deckIndex: number } | null> {
  if (!deck.length) return null;
  const n = deck.length;
  const start = ((deckIndex % n) + n) % n;
  for (let o = 0; o < n; o++) {
    const i = (start + o) % n;
    const k = deck[i]!;
    const v = await fetchVerseByCitationKey(k, signal);
    if (v) return { verse: v, citationKey: k, deckIndex: i };
  }
  return null;
}
