# OBS and Audio Capture

Use three independent captures so one failure does not lose the demo:

1. OBS records the laptop dashboard and terminal preflight.
2. iPhone Screen Recording captures the call UI and hands-free setup.
3. Vapi call artifacts verify whether server-side transcript/audio recording
   exists after the call.

## Before Recording

Close the `.env` tab in VS Code before running preflight. If the editor keeps a
stale `.env` buffer open, it can overwrite the live file and blank the Vapi,
InsForge, or Nebius settings.

Run:

```bash
make recording-preflight
```

This reasserts only non-secret hosted URLs and model defaults, then runs:

- Vapi redacted preflight
- Nebius Token Factory probe
- offline text-to-voice component stress with macOS `say`
- redacted demo stress gate

It does not print or write API keys, phone numbers, transcripts, recordings, or
exact private locations.

The TTS stress creates rehearsal audio under `recordings/tts-stress/`, which is
gitignored. It proves the spoken prompt set exercises local tools and the hosted
InsForge webhook; it does not replace the real Vapi call/STT test.

For the simple variation matrix, run:

```bash
make matrix-stress
```

It covers normal hands-free check-in, protocol, MSDS/safety sheet, hardware,
sensor, shorthand/readback, unknown fallback, and emergency triage.

## OBS Scene

Capture these windows:

- public dashboard: `https://qfdp5nuv.insforge.site/dashboard.html`
- terminal running `make recording-preflight` or `make vapi-wait-call`
- optional Vapi dashboard only if keys, raw phone numbers, transcripts, and
  recordings are hidden

Do not show the `.env` file, Vapi API keys, InsForge keys, Nebius keys, raw
phone numbers, transcripts, recording URLs, or exact private locations.

## iPhone Screen Recording

Before the no-touch section:

1. Add the public dashboard to Home Screen as `PhoneBio`.
2. Grant any permissions during setup.
3. Start iPhone Screen Recording.
4. Place the Vapi call or use the saved contact with Siri.
5. Put the phone on speaker and stop touching it.

If you need room audio in the iPhone recording, enable the Screen Recording
microphone before the take. If Vapi recording is enough, the iPhone recording can
be screen-only and OBS can capture the room.

## Vapi Audio Evidence

Before placing the call, start:

```bash
make vapi-wait-call
```

After the call ends, run:

```bash
make vapi-verify-call
```

The redacted output should show `recordingPresent: true` if Vapi retained call
audio. The helper intentionally does not print the recording URL or download the
file. Export raw audio from the Vapi dashboard only after the take, and keep it
out of git.

## Take Order

1. OBS starts on laptop.
2. iPhone screen recording starts.
3. `make vapi-wait-call` starts in terminal.
4. Call PhoneBio.
5. Run the speaker-only script.
6. End call.
7. `make vapi-verify-call`.
8. Stop iPhone recording.
9. Stop OBS.
10. Save exported Vapi audio locally only if needed for editing.
