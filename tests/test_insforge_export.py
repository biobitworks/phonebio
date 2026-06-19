import json

from scripts import insforge_export


def test_insforge_export_covers_local_content_tables():
    rows = insforge_export.rows()
    tables = {item["table"] for item in rows}

    assert {"protocols", "safety_sheets", "hardware_guides", "sensor_profiles"}.issubset(tables)
    assert all(item["row"]["source_hash"] for item in rows)
    assert all("call_receipts" != item["table"] for item in rows)


def test_insforge_export_preserves_protocol_voice_summary():
    protocol_rows = [item for item in insforge_export.rows() if item["table"] == "protocols"]

    assert any("no headspace" in item["row"]["read_aloud_summary"].lower() for item in protocol_rows)


def test_insforge_export_rows_are_json_serializable():
    for item in insforge_export.rows():
        json.dumps(item)
