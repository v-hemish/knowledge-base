"""Ensure the comprehensive review query set stays valid for capture_guidance_eval_run.py."""

from __future__ import annotations

import json
from pathlib import Path


def _path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "guidance_comprehensive_review_queries.json"


def test_comprehensive_queries_file_valid() -> None:
    raw = json.loads(_path().read_text(encoding="utf-8"))
    assert raw.get("schema") == "guidance_review_queries_v1"
    items = raw.get("items") or []
    assert len(items) >= 25
    ids = [x.get("id") for x in items]
    assert len(ids) == len(set(ids)), "duplicate ids"
    for it in items:
        assert isinstance(it.get("id"), str) and it["id"].strip()
        assert isinstance(it.get("query"), str) and len(it["query"].strip()) >= 8
