import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fieldbio.app import app


client = TestClient(app)


def main() -> None:
    health = client.get("/health")
    health.raise_for_status()
    payload = {
        "message": {
            "toolCalls": [
                {
                    "id": "call_smoke",
                    "function": {
                        "name": "interpret_sensor_report",
                        "arguments": '{"sensor":"barometer","reading":"pressure dropped 4 hPa in 2 hours"}',
                    },
                }
            ]
        }
    }
    webhook = client.post("/webhook", json=payload)
    webhook.raise_for_status()
    print(webhook.json())


if __name__ == "__main__":
    main()
