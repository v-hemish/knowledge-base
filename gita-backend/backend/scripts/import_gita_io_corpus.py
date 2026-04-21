"""
Download the Unlicense Bhagavad Gita JSON corpus from https://github.com/gita/gita
and emit backend-local canonical verse JSON for `scripts/load_verses.py`.

Upstream: verse.json + translation.json (English). We prefer Swami Gambirananda
(author_id=19) when present; otherwise the lowest author_id among English rows.

License: upstream repo is The Unlicense — confirm at
https://github.com/gita/gita/blob/main/LICENSE before redistributing derived JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path


_BASE = "https://raw.githubusercontent.com/gita/gita/main/data"
_PREFERRED_ENGLISH_AUTHOR_ID = 19  # Swami Gambirananda
_TRANSLATION_SOURCE = (
    "Bhagavad Gita JSON (github.com/gita/gita), English translation selected per "
    "verse (prefers Swami Gambirananda where present); repo licensed The Unlicense."
)


def _backend_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _fetch_json(url: str) -> object:
    req = urllib.request.Request(url, headers={"User-Agent": "gita-backend-corpus-import/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310 — intentional URL fetch
        body = resp.read()
    return json.loads(body.decode("utf-8"))


def _pick_english_by_verse(translations: list[dict]) -> dict[int, str]:
    """verse_id -> description (English), deterministic author preference."""
    buckets: dict[int, list[tuple[int, str]]] = {}
    for row in translations:
        if (row.get("lang") or "").lower() != "english":
            continue
        vid = int(row["verse_id"])
        aid = int(row["author_id"])
        desc = (row.get("description") or "").strip()
        if not desc:
            continue
        buckets.setdefault(vid, []).append((aid, desc))

    out: dict[int, str] = {}
    for vid, pairs in buckets.items():
        preferred = [p for p in pairs if p[0] == _PREFERRED_ENGLISH_AUTHOR_ID]
        if preferred:
            out[vid] = preferred[0][1]
            continue
        pairs.sort(key=lambda t: t[0])
        out[vid] = pairs[0][1]
    return out


def _normalize_sanskrit(raw: str) -> str:
    s = (raw or "").replace("\r\n", "\n").strip()
    # Collapse excessive blank lines while keeping pada breaks readable.
    while "\n\n\n" in s:
        s = s.replace("\n\n\n", "\n\n")
    return s.strip()


def _normalize_transliteration(raw: str) -> str:
    s = (raw or "").replace("\r\n", "\n").strip()
    while "\n\n\n" in s:
        s = s.replace("\n\n\n", "\n\n")
    return s.strip()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build canonical JSON from gita/gita upstream data.")
    p.add_argument(
        "--out",
        type=Path,
        default=_backend_root() / "data" / "canonical_bhagavadgita_gita_io.json",
        help="Output path (default: backend/data/canonical_bhagavadgita_gita_io.json)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and validate joins but do not write the output file.",
    )
    args = p.parse_args(argv)

    verses_raw = _fetch_json(f"{_BASE}/verse.json")
    translations_raw = _fetch_json(f"{_BASE}/translation.json")
    if not isinstance(verses_raw, list) or not isinstance(translations_raw, list):
        print("Unexpected upstream JSON root types.", file=sys.stderr)
        return 2

    english = _pick_english_by_verse([dict(x) for x in translations_raw])

    canonical: list[dict] = []
    missing_tr: list[int] = []

    for row in verses_raw:
        r = dict(row)
        vid = int(r["id"])
        ch = int(r["chapter_number"])
        vs = int(r["verse_number"])
        tr = english.get(vid)
        if not tr:
            missing_tr.append(vid)
            continue

        sanskrit = _normalize_sanskrit(str(r.get("text") or ""))
        translit = _normalize_transliteration(str(r.get("transliteration") or ""))
        if not sanskrit or not translit:
            print(f"warning: empty sanskrit/transliteration for verse_id={vid} {ch}.{vs}", file=sys.stderr)

        canonical.append(
            {
                "chapter": ch,
                "verse": vs,
                "citation_key": f"{ch}.{vs}",
                "sanskrit": sanskrit or None,
                "transliteration": translit or None,
                "translation": tr,
                "theme_tags": [],
                "situation_tags": [],
                "use_with_care_tags": [],
                "translation_source": _TRANSLATION_SOURCE,
            }
        )

    if missing_tr:
        print(
            f"error: missing English translation for {len(missing_tr)} verse_id(s), "
            f"first few: {missing_tr[:10]}",
            file=sys.stderr,
        )
        return 3

    canonical.sort(key=lambda x: (int(x["chapter"]), int(x["verse"])))

    out_path = Path(args.out).expanduser()
    if not out_path.is_absolute():
        out_path = (_backend_root() / out_path).resolve()

    payload = {"verses": canonical}
    if args.dry_run:
        print(f"dry-run: would write {len(canonical)} verses to {out_path}")
        return 0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(canonical)} verses to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
