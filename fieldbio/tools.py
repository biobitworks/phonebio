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
    sensors = load_sensors()
    requested_sensor = str(args.get("sensor", "")).lower().strip()
    record = next(
        (
            item
            for item in sensors
            if requested_sensor
            and requested_sensor
            in {str(item.get("id", "")).lower(), *(str(alias).lower() for alias in item.get("aka", []))}
        ),
        None,
    )
    match = None if record else best_match(sensors, _join_args(args, ["sensor", "reading", "context", "description"]))
    if not match or match.score == 0:
        if not record:
            return {
                "status": "not_found",
                "answer": "Sensor type not recognized. Ask for sensor name, units, phone model, and whether the reading was repeated.",
                "confidence": "unknown",
            }
    record = record or match.record
    return {
        "status": "ok",
        "id": record["id"],
        "name": record["name"],
        "measures": record.get("measures"),
        "accuracy": record.get("accuracy", {}),
        "availability": record.get("device_variation"),
        "errorSources": record.get("error_sources", []),
        "calibration": record.get("calibration"),
        "voiceGuidance": record.get("voice_guidance"),
        "measured": args.get("reading"),
        "confidence": record.get("confidence", record.get("accuracy", {}).get("confidence", "unknown")),
        "inferenceBoundary": "Caller-provided readings are guidance, not calibrated instrument results.",
    }


def _sensor_context(args: dict[str, Any]) -> dict[str, Any]:
    fields = {
        "timestamp": args.get("timestamp"),
        "latitude": args.get("latitude"),
        "longitude": args.get("longitude"),
        "locationAccuracyMeters": args.get("locationAccuracyMeters"),
        "altitudeMeters": args.get("altitudeMeters"),
        "barometricPressureHpa": args.get("barometricPressureHpa"),
        "magneticHeadingDegrees": args.get("magneticHeadingDegrees"),
        "magneticFieldMicrotesla": args.get("magneticFieldMicrotesla"),
        "phonePlacement": args.get("phonePlacement"),
        "connectivity": args.get("connectivity"),
        "sensorSummary": args.get("sensorSummary"),
    }
    return {key: value for key, value in fields.items() if value not in (None, "")}


def compress_observation(args: dict[str, Any]) -> dict[str, Any]:
    text_keys = [
        "text",
        "workerRole",
        "locationType",
        "task",
        "material",
        "hazard",
        "sensor",
        "actionNeeded",
        "sensorSummary",
        "connectivity",
        "phonePlacement",
    ]
    text = args.get("text") or "; ".join(f"{key}: {args[key]}" for key in text_keys if args.get(key))
    compact = compress(text)
    return {
        "status": "ok",
        **compact,
        "sensorContext": _sensor_context(args),
        "documentationBoundary": "PhoneBio v1 records caller/app-provided sensor context. It does not automatically read phone sensors without a native app or explicit payload.",
        "magnetometerBoundary": "Phone magnetometers measure local magnetic field/heading, not an object's magnetic moment unless a calibrated external method is supplied.",
    }


def assess_environment_risk(args: dict[str, Any]) -> dict[str, Any]:
    """Deterministic biohazard/extreme-environment triage from spoken/sensor cues."""
    text = _join_args(
        args,
        [
            "hazard",
            "material",
            "audio",
            "vibration",
            "motion",
            "location",
            "connectivity",
            "phonePlacement",
            "sensorSummary",
            "description",
        ],
    ).lower()
    high_terms = {
        "biohazard": "biohazard cue",
        "blood": "potential biological exposure",
        "needle": "sharps exposure",
        "formaldehyde": "toxic chemical exposure",
        "formalin": "toxic chemical exposure",
        "chlorine": "toxic gas risk",
        "ammonia": "toxic gas risk",
        "fuel": "flammable material",
        "fire": "fire",
        "smoke": "smoke inhalation risk",
        "spill": "spill",
        "exposure": "exposure",
        "rotor": "rotating equipment hazard",
        "centrifuge": "rotating equipment hazard",
        "structural": "structural hazard",
        "flood": "flood hazard",
        "heat stroke": "extreme heat illness cue",
        "hypothermia": "extreme cold illness cue",
    }
    medium_terms = {
        "loud": "loud environment",
        "machinery": "machinery nearby",
        "vibration": "vibration",
        "running": "rapid movement",
        "pocket": "pocket sensor placement",
        "data down": "degraded connectivity",
        "voice only": "voice-only connectivity",
        "multiple": "possible multiple speakers",
        "two voices": "possible multiple speakers",
        "overlap": "possible overlapping speakers",
        "wind": "weather/noise interference",
        "heat": "temperature stress",
        "cold": "temperature stress",
    }
    cues = [label for term, label in high_terms.items() if term in text]
    medium_cues = [label for term, label in medium_terms.items() if term in text]

    if any(term in text for term in ["two voices", "multiple", "overlap", "several voices"]):
        people_signal = "possible_multiple_speakers_or_bystanders"
    elif "single" in text or "alone" in text:
        people_signal = "reported_single_person"
    else:
        people_signal = "unknown"

    if cues:
        risk_level = "high"
    elif len(medium_cues) >= 2:
        risk_level = "medium"
    elif medium_cues:
        risk_level = "low_to_medium"
    else:
        risk_level = "unknown"

    actions = ["Continue by voice; do not require app taps or camera input."]
    if risk_level == "high":
        actions.insert(0, "Stop work if safe, isolate the area, and contact the site supervisor or incident lead.")
    elif risk_level == "medium":
        actions.insert(0, "Slow down, repeat the critical reading, and confirm hazard, location, and people/injury status.")
    else:
        actions.insert(0, "Ask one clarifying question: hazard, location, or sensor units.")
    if any(term in text for term in ["formaldehyde", "formalin", "chlorine", "ammonia", "fuel", "smoke"]):
        actions.append("Move upwind or increase distance if safe; avoid inhalation and ignition sources.")
    if any(term in text for term in ["biohazard", "blood", "needle", "sharps"]):
        actions.append("Avoid contact, preserve PPE, and treat exposure status as safety-critical.")

    compact = compress(args.get("description") or text)
    return {
        "status": "ok",
        "riskLevel": risk_level,
        "peopleSignal": people_signal,
        "highRiskCues": cues,
        "contextCues": medium_cues,
        "actions": actions,
        "compactFieldLine": compact["field_line"],
        "voiceReadback": compact["voice_readback"],
        "confidence": "medium" if cues or medium_cues else "low",
        "inferenceBoundary": "Single-phone sensors can flag risk context and possible voice overlap; they do not prove exact speaker count, identity, or calibrated exposure level.",
    }


TOOLS = {
    "get_protocol": get_protocol,
    "get_safety_sheet": get_safety_sheet,
    "troubleshoot_hardware": troubleshoot_hardware,
    "interpret_sensor_report": interpret_sensor_report,
    "compress_observation": compress_observation,
    "assess_environment_risk": assess_environment_risk,
}
