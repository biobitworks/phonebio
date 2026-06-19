#!/usr/bin/env python3
"""Seed InsForge tables from the local content files (idempotent upsert).

Runs SQL through `npx @insforge/cli db query` (project_admin, bypasses RLS), so
no API key is handled in code. Re-running updates existing rows by id.

Usage: python3 scripts/seed_insforge.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fieldbio.content import (  # noqa: E402
    load_protocols,
    load_sds,
    load_sensors,
    load_troubleshooting,
)

SENSOR_SOURCE = "content/sensors/sensors.json"


def lit(v) -> str:
    if v is None:
        return "NULL"
    return "'" + str(v).replace("'", "''") + "'"


def jlit(v) -> str:
    return "'" + json.dumps(v, ensure_ascii=False).replace("'", "''") + "'::jsonb"


def sha(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def run_sql(sql: str) -> None:
    proc = subprocess.run(
        ["npx", "-y", "@insforge/cli", "db", "query", sql, "--json"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(proc.stdout[-500:])
        print(proc.stderr[-500:], file=sys.stderr)
        raise SystemExit(f"db query failed (exit {proc.returncode})")


def upsert(table: str, cols: list[str], rows: list[list[str]]) -> None:
    if not rows:
        print(f"  {table}: nothing to seed")
        return
    values = ",\n  ".join("(" + ", ".join(r) + ")" for r in rows)
    updates = ", ".join(f"{c}=excluded.{c}" for c in cols if c != "id")
    sql = (
        f"insert into public.{table} ({', '.join(cols)}) values\n  {values}\n"
        f"on conflict (id) do update set {updates};"
    )
    run_sql(sql)
    print(f"  {table}: upserted {len(rows)} row(s)")


def main() -> None:
    print("Seeding InsForge from local content...")

    # protocols
    cols = ["id", "title", "domain", "keywords", "hazards", "read_aloud_summary",
            "body_markdown", "source_path", "source_hash"]
    rows = [[
        lit(p["id"]), lit(p["title"]), lit(p.get("domain")),
        jlit(p.get("keywords", [])), jlit(p.get("hazards", [])),
        lit(p.get("read_aloud_summary") or ""), lit(p["body"]),
        lit(p.get("source_path", "")), lit(sha(p)),
    ] for p in load_protocols()]
    upsert("protocols", cols, rows)

    # safety_sheets
    cols = ["id", "name", "synonyms", "hazards", "ppe", "first_aid",
            "disclaimer", "spill", "storage", "source_path", "source_hash"]
    rows = [[
        lit(s["id"]), lit(s["name"]), jlit(s.get("synonyms", [])),
        jlit(s.get("hazards", [])), jlit(s.get("ppe", [])),
        jlit(s.get("first_aid", {})), lit(s.get("_disclaimer") or s.get("disclaimer") or ""),
        lit(s.get("spill")), lit(s.get("storage")),
        lit(s.get("source_path", "")), lit(sha(s)),
    ] for s in load_sds()]
    upsert("safety_sheets", cols, rows)

    # hardware_guides
    cols = ["id", "device", "symptom", "keywords", "steps", "escalate_if",
            "source_path", "source_hash"]
    rows = [[
        lit(t["id"]), lit(t["device"]), lit(t["symptom"]),
        jlit(t.get("keywords", [])), jlit(t.get("steps", [])),
        lit(t.get("escalate_if")), lit(t.get("source_path", "")), lit(sha(t)),
    ] for t in load_troubleshooting()]
    upsert("hardware_guides", cols, rows)

    # sensor_profiles
    cols = ["id", "name", "measures", "accuracy", "error_sources", "availability",
            "calibration", "voice_guidance", "source_path", "source_hash"]
    rows = [[
        lit(s["id"]), lit(s.get("name")), lit(s.get("measures")),
        jlit(s.get("accuracy", {})), jlit(s.get("error_sources", [])),
        lit(s.get("device_variation")), lit(s.get("calibration")),
        lit(s.get("voice_guidance")), lit(SENSOR_SOURCE), lit(sha(s)),
    ] for s in load_sensors()]
    upsert("sensor_profiles", cols, rows)

    print("Done.")


if __name__ == "__main__":
    main()
