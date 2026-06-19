"""Vapi tool implementations backed by local content."""
from __future__ import annotations

from typing import Any

from .content import best_match, load_protocols, load_sds, load_sensors, load_troubleshooting
from .shorthand import compress


def _join_args(args: dict[str, Any], keys: list[str]) -> str:
    return " ".join(str(args.get(key, "")) for key in keys if args.get(key))


def get_protocol(args: dict[str, Any]) -> dict[str, Any]:
    match = best_match(load_protocols(), _join_args(args, ["task", "organism", "hazard", "description"]))
    if not match or match.score == 0:
        return {
            "status": "not_found",
            "answer": "No local protocol matched. Stop and call the site supervisor before improvising.",
            "sourceIds": [],
        }
    record = match.record
    return {
        "status": "ok",
        "id": record["id"],
        "title": record["title"],
        "readAloudSummary": record.get("read_aloud_summary") or record.get("title"),
        "hazards": record.get("hazards", []),
        "body": record["body"],
        "sourceIds": [record["source_path"]],
    }


def get_safety_sheet(args: dict[str, Any]) -> dict[str, Any]:
    match = best_match(load_sds(), _join_args(args, ["substance", "hazard", "description"]))
    if not match or match.score == 0:
        return {
            "status": "not_found",
            "answer": "No local safety summary matched. Isolate the material if safe, avoid mixing chemicals, and escalate.",
            "sourceIds": [],
        }
    record = match.record
    return {
        "status": "ok",
        "id": record["id"],
        "name": record["name"],
        "disclaimer": record.get("_disclaimer"),
        "hazards": record.get("hazards", []),
        "ppe": record.get("ppe", []),
        "firstAid": record.get("first_aid", {}),
        "spill": record.get("spill"),
        "sourceIds": [record["source_path"]],
    }


def troubleshoot_hardware(args: dict[str, Any]) -> dict[str, Any]:
    match = best_match(load_troubleshooting(), _join_args(args, ["device", "symptom", "description"]))
    if not match or match.score == 0:
        return {
            "status": "not_found",
            "answer": "No local hardware guide matched. Power down if unsafe and call the equipment owner.",
            "sourceIds": [],
        }
    record = match.record
    return {
        "status": "ok",
        "id": record["id"],
        "device": record["device"],
        "symptom": record["symptom"],
        "steps": record.get("steps", []),
        "escalateIf": record.get("escalate_if"),
        "sourceIds": [record["source_path"]],
    }


def interpret_sensor_report(args: dict[str, Any]) -> dict[str, Any]:
    match = best_match(load_sensors(), _join_args(args, ["sensor", "reading", "context", "description"]))
    if not match or match.score == 0:
        return {
            "status": "not_found",
            "answer": "Sensor type not recognized. Ask for sensor name, units, phone model, and whether the reading was repeated.",
            "confidence": "unknown",
        }
    record = match.record
    return {
        "status": "ok",
        "id": record["id"],
        "name": record["name"],
        "measures": record.get("measures"),
        "accuracy": record.get("accuracy", {}),
        "errorSources": record.get("error_sources", []),
        "calibration": record.get("calibration"),
        "voiceGuidance": record.get("voice_guidance"),
        "measured": args.get("reading"),
        "confidence": record.get("confidence", record.get("accuracy", {}).get("confidence", "unknown")),
        "inferenceBoundary": "Caller-provided readings are guidance, not calibrated instrument results.",
    }


def compress_observation(args: dict[str, Any]) -> dict[str, Any]:
    text = args.get("text") or "; ".join(f"{key}: {value}" for key, value in args.items())
    return {"status": "ok", **compress(text)}


TOOLS = {
    "get_protocol": get_protocol,
    "get_safety_sheet": get_safety_sheet,
    "troubleshoot_hardware": troubleshoot_hardware,
    "interpret_sensor_report": interpret_sensor_report,
    "compress_observation": compress_observation,
}

