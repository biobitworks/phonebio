# Test Number + Accessibility Run

Use this only for controlled rehearsal. For the final live demo, prefer your
phone calling PhoneBio.

## Simple Flow

1. Vapi answers fast and speaks first.
2. InsForge captures every lab-related spoken turn in background text
   processing.
3. One keyword path runs when needed: SDS, protocol, hardware, or sensor.
4. Nebius stays fast for voice; heavy 70B bursts are reserved for complex or
   emergency backend processing.

## Dry Run

```bash
make test-number-call
```

This prints the redacted Vapi test-number direction and the script variations.
It does not place a call.

## Live Test-Number Call

```bash
make test-number-call-live
```

This spends Vapi credits and calls the PhoneBio number from the Vapi test
number. It is useful for connectivity checks, but it can create echo or
agent-to-agent audio. Use a human phone call for the judged demo when possible.

## Accessibility Variations

- Siri: "Hey Siri, call PhoneBio."
- Voice Control: enable before the demo; use "Show names" and "Tap PhoneBio"
  if the saved Home Screen link is needed.
- Switch Control or AssistiveTouch: preconfigure a saved action before the
  field/no-touch portion.
- Noisy stage: keep phrases short and say "speaker only" at the start.

## Spoken Lines

1. "PhoneBio, I am on speaker only and cannot touch the phone."
2. "Field note. Observed three juvenile specimens near the burrow at 12
   meters, 18 degrees."
3. "Low-level formaldehyde cleanup. No fire. No skin contact. I forgot the SDS
   location step."
4. "I am near open ventilation. Eyewash is across the room. The spill kit is
   behind me. The exit is clear."
5. Optional: "Now there is a small fire and I cannot reach emergency services."

## What To Say If Asked

"We keep the call simple: capture every lab utterance, do one lookup when a
keyword requires it, answer by voice, and escalate only when risk or complexity
increases."

Do not commit raw transcripts, private phone numbers, API keys, recording URLs,
or exact private locations to GitHub.
