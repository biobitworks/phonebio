# ExecuTorch Local Orchestrator

PhoneBio can use ExecuTorch as the future on-device runtime for a small
quantized environmental triage model.

## Demo Boundary

The current public dashboard shows a simulated ExecuTorch local gate. It does
not run a real `.pte` model in the hosted browser page.

The simulation is still useful for the video because it shows the intended
resource-routing behavior:

- Low-risk sensor context stays local.
- Noisy audio asks one confirmation question before using the signal.
- Biohazard or emergency cues go to priority voice handling.
- Cloud/GPU resources are reserved for heavier downstream processing, not every
  raw sensor tick.

## Target Runtime

ExecuTorch is PyTorch's edge inference runtime for mobile and embedded devices.
The target PhoneBio path is:

```text
phone sensors -> normalized low-level features -> tiny PyTorch classifier ->
quantize/export to ExecuTorch .pte -> on-device triage label -> Vapi/InsForge route
```

## Minimal Model Shape

Inputs should be small numeric features, not raw audio or private transcripts:

- audio RMS / rough overlap flag
- accelerometer vibration score
- gyroscope motion score
- GPS accuracy bucket
- barometer trend bucket
- BLE/UWB nearby-device count bucket
- phone placement flag

Outputs:

- `normal_call`
- `sensor_context`
- `noisy_confirmation`
- `emergency_priority`

## Implementation Plan

1. Train or hand-calibrate a tiny PyTorch MLP or tree-like classifier on
   synthetic and field-collected labeled sensor summaries.
2. Quantize to INT8 or INT4 where supported by the target backend.
3. Export to ExecuTorch `.pte`.
4. Run locally in an iOS/Android wrapper.
5. Send only the low-cardinality triage label and confidence to Vapi/InsForge
   unless the caller opts into sharing richer context.

## Demo Line

"This is the local gate we would run with ExecuTorch: a tiny quantized model
classifies low-level phone signals before deciding whether to stay local, ask a
confirmation question, or escalate the call."

## References

- ExecuTorch documentation: https://docs.pytorch.org/executorch/stable/index.html
- ExecuTorch project: https://github.com/pytorch/executorch
