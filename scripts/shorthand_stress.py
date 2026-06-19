"""Stress lab jargon through shorthand compression and voice readback."""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from fieldbio.shorthand import compress


CASES = [
    {
        "id": "legacy-centrifuge-balance",
        "spoken": "Stop work. The legacy centrifuge rotor vibrates at 5000 rpm after balancing two 1.5 ml tubes.",
        "must_keep": ["stop", "centrifuge", "rotor", "rpm"],
        "measure_units": ["rpm", "ml"],
    },
    {
        "id": "pipette-aliquot-control",
        "spoken": "Aliquot 20 ul buffer with the micropipette, then run a negative control and positive control.",
        "must_keep": ["aliquot", "buffer", "micropipette", "control"],
        "measure_units": ["ul"],
    },
    {
        "id": "formalin-ppe-sds",
        "spoken": "Formaldehyde spill near the old incubator. Wear personal protective equipment and read the safety data sheet.",
        "must_keep": ["formaldehyde", "incubator", "personal", "safety"],
        "measure_units": [],
    },
    {
        "id": "pcr-no-template",
        "spoken": "Polymerase chain reaction failed. No template control amplified and the sample is contamination suspect.",
        "must_keep": ["polymerase", "control", "sample", "contamination"],
        "measure_units": [],
    },
]


def _case_result(case: dict) -> dict:
    result = compress(case["spoken"])
    readback = result["voice_readback"].lower()
    token_originals = " ".join(str(item["from"]).lower() for item in result["token_map"])
    preserved = all(term in readback or term in token_originals for term in case["must_keep"])
    units = [item["unit"] for item in result["measurements"]]
    units_ok = all(unit in units for unit in case["measure_units"])
    return {
        "id": case["id"],
        "passed": preserved and units_ok and result["compression_ratio"] < 0.8,
        "spoken": case["spoken"],
        "fieldLine": result["field_line"],
        "voiceReadback": result["voice_readback"],
        "compressionRatio": result["compression_ratio"],
        "measurements": result["measurements"],
        "preservedCriticalTerms": preserved,
        "measurementUnitsOk": units_ok,
    }


def main() -> None:
    cases = [_case_result(case) for case in CASES]
    report = {
        "scenario": "lab-jargon-gregg-style-shorthand-stress",
        "summary": {
            "cases": len(cases),
            "passed": all(case["passed"] for case in cases),
            "compressionRatioMax": max(case["compressionRatio"] for case in cases),
        },
        "cases": cases,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    if not report["summary"]["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
