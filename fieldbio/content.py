"""Offline content loading and search for PhoneBio."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import CONTENT_DIR


@dataclass(frozen=True)
class Match:
    record: dict[str, Any]
    score: int


def _normalize(value: Any) -> str:
    return str(value or "").lower()


def _terms(query: str) -> list[str]:
    return [term for term in re.split(r"[^a-z0-9]+", query.lower()) if len(term) > 1]


def _score(record: dict[str, Any], query: str) -> int:
    searchable = json.dumps(record, sort_keys=True).lower()
    return sum(1 for term in _terms(query) if term in searchable)


def best_match(records: list[dict[str, Any]], query: str) -> Match | None:
    if not records:
        return None
    matches = [Match(record, _score(record, query)) for record in records]
    matches.sort(key=lambda item: item.score, reverse=True)
    return matches[0]


def _parse_frontmatter(markdown: str) -> tuple[dict[str, Any], str]:
    if not markdown.startswith("---"):
        return {}, markdown
    _, frontmatter, body = markdown.split("---", 2)
    meta: dict[str, Any] = {}
    current_key: str | None = None
    for raw_line in frontmatter.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("-") and current_key:
            meta.setdefault(current_key, []).append(line.lstrip("- ").strip())
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        current_key = key
        if value.startswith("[") and value.endswith("]"):
            meta[key] = [item.strip() for item in value.strip("[]").split(",") if item.strip()]
        elif value in {">", "|"}:
            meta[key] = ""
        else:
            meta[key] = value
    return meta, body.strip()


def _load_markdown_dir(path: Path) -> list[dict[str, Any]]:
    records = []
    for file_path in sorted(path.glob("*.md")):
        text = file_path.read_text(encoding="utf-8")
        meta, body = _parse_frontmatter(text)
        records.append(
            {
                "id": meta.get("id", file_path.stem),
                "title": meta.get("title", file_path.stem.replace("_", " ")),
                "keywords": meta.get("keywords", []),
                "hazards": meta.get("hazards", []),
                "read_aloud_summary": meta.get("read_aloud_summary", ""),
                "body": body,
                "source_path": str(file_path.relative_to(CONTENT_DIR.parent)),
            }
        )
    return records


def _load_json_dir(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(file_path.read_text(encoding="utf-8")) | {
            "source_path": str(file_path.relative_to(CONTENT_DIR.parent))
        }
        for file_path in sorted(path.glob("*.json"))
    ]


def load_protocols() -> list[dict[str, Any]]:
    return _load_markdown_dir(CONTENT_DIR / "protocols")


def load_sds() -> list[dict[str, Any]]:
    return _load_json_dir(CONTENT_DIR / "sds")


def load_troubleshooting() -> list[dict[str, Any]]:
    return _load_json_dir(CONTENT_DIR / "troubleshooting")


def load_sensors() -> list[dict[str, Any]]:
    data = json.loads((CONTENT_DIR / "sensors" / "sensors.json").read_text(encoding="utf-8"))
    return data.get("sensors", [])

