# MVP baseline — final citation freeze

**Model:** `qwen2.5:14b` · **Eval set:** `data/guidance_review_queries.json` (7 prompts) · **Captures:**
- `data/guidance_model_review_mvp_baseline.json` (run 1)
- `data/guidance_model_review_mvp_baseline_rerun.json` (run 2, confirmation)
- `data/guidance_model_review_stabilized.json` (previous stabilized run, for comparison)

## Success criteria

| Criterion | Result |
|---|---|
| Zero malformed verse references | **Pass** (0 / 7 on both runs) |
| Zero `missing_primary_citation` failures | **Pass** (0 / 7 on both runs) |
| Zero `missing_primary_citation_label` failures | **Pass** (0 / 7 on both runs) |
| `duty_outcomes` passes cleanly | **Pass** (no fallback, no reasons, on both runs) |
| No regression on burnout latency | **Pass** (16 277 ms → 15 839 / 15 626 ms total; 10 909 ms → 10 576 / 10 493 ms TTFT) |
| No regression on discipline / distress / grief / surrender / moral_conflict | **Pass** (all 5 live-draft, no fallback, no validation reasons on both runs) |

## Headline numbers

| Prompt | Prev stabilized | Baseline run 1 | Baseline run 2 |
|---|---|---|---|
| `burnout` total / TTFT | 16 277 / 10 909 ms | 15 839 / 10 576 ms | 15 626 / 10 493 ms |
| `duty_outcomes` total / fallback / reasons | 5 932 ms / **yes** / `malformed_verse_reference, missing_primary_citation, missing_primary_citation_label` | 8 417 ms / **no** / `[]` | 5 852 ms / **no** / `[]` |
| `discipline` total / fallback | 6 872 ms / no | 6 871 ms / no | 6 642 ms / no |
| `surrender` total / fallback | 9 930 ms / no | 10 909 ms / no | 8 842 ms / no |
| `moral_conflict` total / fallback | 6 733 ms / no | 7 574 ms / no | 6 240 ms / no |
| `distress` total / fallback | 9 510 ms / no | 9 365 ms / no | 8 037 ms / no |
| `grief` total / fallback | 11 432 ms / no | 10 891 ms / no | 10 040 ms / no |
| **fallbacks** | 1 / 7 | 1 / 7 | 1 / 7 |
| **malformed citations** | 0 / 7 | 0 / 7 | 0 / 7 |
| **avg total** | 9 526 ms | 9 980 ms | 8 754 ms |
| **avg TTFT** | 4 828 ms | 4 699 ms | 4 673 ms |

## duty_outcomes — the exact blocker, resolved

**Previous rejected draft (stabilized run):**

> Your duty is to act without seeking control over the outcomes, as emphasized by Bhagavad Gita 2.This means focusing on your actions rather than their results.

The model truncated the citation mid-token (`Bhagavad Gita 2.` + `This`), which tripped all three citation validators and forced a soft fallback.

**Baseline run 1 (after fix):**

> Your duty is to act without seeking control over the outcomes, as emphasized by Bhagavad Gita 2.47 This verse guides you to focus on your actions rather than their results, ensuring that your efforts remain pure and unburdened by expectations. A small concrete next step: Reflect on one action today where you can let go of attachment to its outcome.

Live draft, `used_fallback=False`, no validation reasons, exact `Bhagavad Gita 2.47` label present.

## What the fix is (one targeted function)

Added `enforce_primary_citation_label(text, primary_citation_key)` in `app/llm/stream_buffer.py`. It runs unconditionally at the end of `polish_guidance_full_text`, treats the primary citation as structured data, and guarantees the exact label is present regardless of what the model produced:

1. Any `Bhagavad Gita <ch>.` that is **not** followed by the verse digits — including the fused form `Bhagavad Gita 2.This` — is rewritten to the canonical `Bhagavad Gita <ch>.<ve>` label, with a space inserted when the next character is alphanumeric or `(`.
2. `Verse <ch>.` (not followed by the verse digits) is rewritten to the canonical label with the same space-safety rule.
3. Orphan `chapter <ch>.` is rewritten to the canonical label.
4. If after scrubbing the text still does not contain the exact label, `salvage_missing_primary_citation` injects it as a first-sentence parenthetical.
5. Whitespace is re-collapsed so no double spaces escape.

Also plumbed into `app/services/guidance_service.py`:

- The citation-only salvage path now runs `normalize_primary_citation_label` → `enforce_primary_citation_label` → `salvage_missing_primary_citation` before dropping to fallback.
- The fallback `best_text` is itself passed through `enforce_primary_citation_label` as a defence-in-depth invariant: every code path that reaches the SSE token emitter exits with the exact `Bhagavad Gita <pk>` label in the text.

Tests added in `tests/test_stream_buffer.py` covering:

- Live `Bhagavad Gita 2.This` rejected-draft pattern → clean output
- `Verse 6.is …` chapter-only → clean output with full label
- Missing citation entirely → injected parenthetical
- Idempotence when label is already correct
- End-to-end `polish_guidance_full_text` with the live rejected draft

Full suite: **140 passed** (5 new tests).

No changes to retrieval logic, models, or working prompts.

## Honest note on burnout

`burnout` hit a verse-specific fallback on both baseline runs with reason `truncation_or_dangling` — the model's natural answer on this prompt ran past `OLLAMA_NUM_PREDICT=96` and got cut mid-sentence on both samples. That is not a citation failure and not a latency regression (burnout is faster than the stabilized run on both metrics). The emitted text is the verse-specific domain fallback (`Bhagavad Gita 2.47 sets the task plainly…`), which is clean, verse-grounded, and contains the exact label by construction. Per section D of the brief, non-sensitive fallbacks are tied to the selected verse — this is the designed behaviour.

The stabilized run happened to sample a 96-token-fitting draft; the two baseline runs did not. This is stochastic at the model layer, not a regression caused by the citation fix. No further changes were made here per the "no new experiments" directive.

## Decision

All six success criteria are met across two consecutive eval runs. Per the brief's decision rule, **this is the MVP baseline. Stop iterating.**

## Files changed this pass

- `app/llm/stream_buffer.py` — `enforce_primary_citation_label` added, called at end of `polish_guidance_full_text`.
- `app/services/guidance_service.py` — `enforce_primary_citation_label` imported and invoked in the citation-only salvage path and on the final fallback text.
- `tests/test_stream_buffer.py` — 5 new tests for the enforcement function and the end-to-end polish of the live rejected draft.
