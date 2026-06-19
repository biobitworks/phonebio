"""Export local PhoneBio content as InsForge-ready JSONL.

This does not contact InsForge. It gives the operator a deterministic seed file
for review before any backend write is approved.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fieldbio.config import CONTENT_DIR
from fieldbio.content import load_protocols, load_sds, load_sensors, load_troubleshooting


def _source_hash(source_path: str) -> str:
    return hashlib.sha256((REPO_ROOT / source_path).read_bytes()).hexdigest()


def _emit(table: str, row: dict[str, Any]) -> dict[str, Any]:
    return {"table": table, "row": row}


def protocol_rows() -> Iterable[dict[str, Any]]:
    for record in load_protocols():
        yield _emit(
            "protocols",
            {
                "id": record["id"],
                "title": record["title"],
                "domain": record.get("domain"),
                "keywords": record.get("keywords", []),
                "hazards": record.get("hazards", []),
                "read_aloud_summary": record.get("read_aloud_summary"),
                "body_markdown": record["body"],
                "source_path": record["source_path"],
                "source_hash": _source_hash(record["source_path"]),
            },
        )


def safety_rows() -> Iterable[dict[str, Any]]:
    for record in load_sds():
        yield _emit(
            "safety_sheets",
            {
                "id": record["id"],
                "name": record["name"],
                "synonyms": record.get("synonyms", []),
                "hazards": record.get("hazards", []),
                "ppe": record.get("ppe", []),
                "first_aid": record.get("first_aid", {}),
                "disclaimer": record.get("_disclaimer"),
                "source_path": record["source_path"],
                "source_hash": _source_hash(record["source_path"]),
            },
        )


def hardware_rows() -> Iterable[dict[str, Any]]:
    for record in load_troubleshooting():
        yield _emit(
            "hardware_guides",
            {
                "id": record["id"],
                "device": record["device"],
                "symptom": record["symptom"],
                "keywords": record.get("keywords", []),
                "steps": record.get("steps", []),
                "escalate_if": record.get("escalate_if"),
                "source_path": record["source_path"],
                "source_hash": _source_hash(record["source_path"]),
            },
        )


def sensor_rows() -> Iterable[dict[str, Any]]:
    sensor_source = str((CONTENT_DIR / "sensors" / "sensors.json").relative_to(REPO_ROOT))
    sensor_hash = _source_hash(sensor_source)
    for record in load_sensors():
        yield _emit(
            "sensor_profiles",
            {
                "id": record["id"],
                "name": record["name"],
                "measures": record["measures"],
                "accuracy": record.get("accuracy", {}),
                "error_sources": record.get("error_sources", []),
                "availability": record.get("device_variation"),
                "calibration": record.get("calibration"),
                "voice_guidance": record.get("voice_guidance"),
                "source_path": sensor_source,
                "source_hash": sensor_hash,
            },
        )


def rows() -> list[dict[str, Any]]:
    return [*protocol_rows(), *safety_rows(), *hardware_rows(), *sensor_rows()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Export local PhoneBio content as InsForge seed JSONL.")
    parser.add_argument("--summary", action="store_true", help="Print table counts instead of JSONL rows.")
    args = parser.parse_args()

    exported = rows()
    if args.summary:
        counts: dict[str, int] = {}
        for item in exported:
            counts[item["table"]] = counts.get(item["table"], 0) + 1
        print(json.dumps({"tables": counts, "rows": len(exported)}, indent=2, sort_keys=True))
        return

    for item in exported:
        print(json.dumps(item, sort_keys=True))


if __name__ == "__main__":
    main()
