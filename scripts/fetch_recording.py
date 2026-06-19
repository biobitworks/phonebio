#!/usr/bin/env python3
"""Fetch the most recent Vapi call's recording + transcript (for the video).

    make recording     # or:  python3 scripts/fetch_recording.py
Saves audio to recordings/<callId>.mp3 (gitignored) and prints the transcript.
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
    print("No calls yet. Call +1 541-526-9723, then re-run."); sys.exit(0)
target = next((c for c in calls if rec_url(c)), calls[0])
art = target.get("artifact") or {}
url = rec_url(target)
print("call:", target.get("id"), "| status:", target.get("status"), "| ended:", target.get("endedAt"))
print("recording:", url)
print("stereo:", art.get("stereoRecordingUrl"))
tr = target.get("transcript") or art.get("transcript")
if tr:
    print("\n--- transcript ---\n" + tr[:2000])
if url:
    os.makedirs("recordings", exist_ok=True)
    ext = "wav" if ".wav" in (url or "") else "mp3"
    out = f"recordings/{target.get('id')}.{ext}"
    subprocess.run(["curl", "-sL", url, "-o", out])
    print("\nsaved ->", out)
else:
    print("\n(no recording URL yet — it can take a moment after the call ends)")
