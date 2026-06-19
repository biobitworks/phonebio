import asyncio

from scripts.demo_call import run_demo


def test_demo_call_script_passes_expected_local_turns():
    report = asyncio.run(run_demo())

    assert report["summary"] == {"turns": 5, "passed": True}
    assert [turn.get("id") for turn in report["turns"][:4]] == [
        "water_quality_grab_sample",
        "formaldehyde_solution",
        "centrifuge_vibration",
        "barometer",
    ]
    assert [turn["tool"] for turn in report["turns"]] == [
        "get_protocol",
        "get_safety_sheet",
        "troubleshoot_hardware",
        "interpret_sensor_report",
        "compress_observation",
    ]
    assert all(turn["status"] == "ok" for turn in report["turns"])
