# Vapi Assistants, Tools, And Squads

## Live Demo Choice

Use one Vapi **Assistant** for the demo.

Reason: the call already failed from slow routing/tool loops. One assistant with
a simple triage ladder is the lowest-risk live path.

## Current Live Resources

### Assistant

**PhoneBio Field Biology Worker**

- answers the phone;
- asks one question at a time;
- keeps replies short;
- routes through the InsForge custom LLM proxy;
- uses the fast Nebius model for voice;
- lets InsForge process transcript/tool work in the background.

### Tools

Use the five existing assistant tool definitions. If adding them manually in
Vapi, the request URL is:

```text
https://qfdp5nuv.function2.insforge.app/phonebio-vapi-webhook
```

Do not use `https://www.vapi.ai` as the tool URL.

Core tools:

- `compress_observation` - every lab-related spoken turn / field notes.
- `get_safety_sheet` - chemicals such as formaldehyde/formalin.
- `get_protocol` - procedure or experiment questions.
- `troubleshoot_hardware` - device or old-equipment symptoms.
- `interpret_sensor_report` - phone/laptop sensor text summaries.

Keep the schema locked and define only the parameters each tool needs. The
checked-in assistant template already contains the working schemas.

### Squads

Do not route the live demo through a Squad today.

Squads are the v2 design:

- Field Notes Assistant
- Chemical Safety Assistant
- Hardware/Sensor Assistant
- Emergency Triage Assistant

That is cleaner long-term, but it adds handoff conditions and another failure
surface. For the live demo, the single assistant triages internally:

1. Capture the utterance.
2. Run one lookup if a keyword needs it.
3. Speak a short answer.
4. Escalate only for emergency, uncertainty, or complex reasoning.
