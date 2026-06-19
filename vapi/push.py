"""Create a Vapi assistant from the local template."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from fieldbio.vapi_client import api_key_from_env, assistant_payload, create_assistant


def main() -> None:
    try:
        print(create_assistant(api_key_from_env(), assistant_payload()))
    except Exception as error:
        print(f"Vapi assistant creation failed: {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
