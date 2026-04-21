/**
 * SOURCE DATA (for you or your ingestion pipeline)
 * -----------------------------------------------
 * The app expects verse **text** to match what the FastAPI backend serves from SQLite
 * (`RetrieveVerseCard`: citation_key, chapter, verse, translation, transliteration, sanskrit, …).
 *
 * **Canonical file already in repo:** `backend/data/canonical_bhagavadgita_gita_io.json`
 * - Array under `verses`, each object:
 *   - `citation_key` (string, e.g. `"5.12"`)
 *   - `chapter` (number), `verse` (number)
 *   - `translation` (non-empty English; this is what users read)
 *   - `transliteration`, `sanskrit` (optional strings)
 *   - optional `theme_tags`, `situation_tags`, `use_with_care_tags`, `translation_source`
 *
 * **If a verse in SQLite has a “not translated” placeholder** in `translation`, the
 * practice UI will skip it (see `verseQuality.ts`). Re-seed the DB from the canonical JSON
 * for those rows, or replace `translation` with your own approved English.
 *
 * **Daily-practice seed:** `backend/data/gita_daily_practice_app_spec_with_sanskrit.json`
 * (`starter_verse_pack`). Keep `PRACTICE_DECK_CITATION_KEYS` in `dailyDeck.ts` aligned with
 * that pack for **Today** only. **Learn** uses `GET /api/v1/verses/citation-index` (all
 * non-placeholder verses in SQLite, e.g. 701).
 *
 * **Retrieve:** queries like `Bhagavad Gita 2.47` are resolved by explicit citation lookup
 * on the backend (FTS does not index `citation_key`), so practice fetches work even when the
 * translation text does not contain those words.
 *
 * **Fast practice fetch:** `GET /api/v1/verses/citation-index`, `GET /api/v1/verses/by-key/{citation_key}`, and
 * `POST /api/v1/verses/by-keys` return DB-backed data without the full retrieve pipeline.
 */

export {};
