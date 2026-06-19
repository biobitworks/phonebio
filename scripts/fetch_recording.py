#!/usr/bin/env python3
"""Fetch the most recent Vapi call recording for the video.

    make recording     # or:  python3 scripts/fetch_recording.py
Saves audio to recordings/<callId>.mp3 (gitignored). Does not print recording
URLs, transcripts, phone numbers, or summaries.
"""
import json, os, subprocess, sys

env = {}
for line in open(".env"):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); env[k] = v
KEY = env.get("VAPI_PRIVATE_KEY") or env.get("VAPI_API_KEY")


def curl(path):
    out = subprocess.run(["curl", "-s", f"https://api.vapi.ai{path}", "-H", f"Authorization: Bearer {KEY}"],
                         capture_output=True, text=True).stdout
    try: return json.loads(out)
    except Exception: return {}


def rec_url(c):
    art = c.get("artifact") or {}
    return (art.get("recordingUrl") or art.get("recording", {}).get("combinedUrl")
            or art.get("stereoRecordingUrl") or c.get("recordingUrl"))


calls = curl("/call?limit=10")
if not isinstance(calls, list) or not calls:
    print(json.dumps({"saved": False, "reason": "no_calls"}, indent=2)); sys.exit(0)
target = next((c for c in calls if rec_url(c)), calls[0])
art = target.get("artifact") or {}
url = rec_url(target)
if url:
    os.makedirs("recordings", exist_ok=True)
    ext = "wav" if ".wav" in (url or "") else "mp3"
    out = f"recordings/{target.get('id')}.{ext}"
    subprocess.run(["curl", "-sL", url, "-o", out])
    print(json.dumps({
        "saved": True,
        "path": out,
        "callId": target.get("id"),
        "status": target.get("status"),
        "endedReason": target.get("endedReason"),
        "recordingPresent": True,
        "transcriptPresent": bool(target.get("transcript") or art.get("transcript")),
    }, indent=2, sort_keys=True))
else:
    print(json.dumps({
        "saved": False,
        "callId": target.get("id"),
        "status": target.get("status"),
        "endedReason": target.get("endedReason"),
        "recordingPresent": False,
        "transcriptPresent": bool(target.get("transcript") or art.get("transcript")),
        "reason": "recording_url_not_available_yet",
    }, indent=2, sort_keys=True))
