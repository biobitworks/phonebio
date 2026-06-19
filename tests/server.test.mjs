import test from "node:test";
import assert from "node:assert/strict";
import { clearSignals, handleWebhook, latestSignals, recordSignal } from "../src/server.mjs";

test("handles Vapi-style function arguments", async () => {
  const result = await handleWebhook({
    message: {
      toolCalls: [
        {
          id: "call_1",
          function: {
            name: "get_safety_sheet",
            arguments: JSON.stringify({ substance: "ethanol spill" })
          }
        }
      ]
    }
  });

  assert.equal(result.results.length, 1);
  assert.equal(result.results[0].toolCallId, "call_1");
  assert.equal(result.results[0].result.status, "ok");
  assert.match(result.results[0].result.substance, /ethanol/i);
});

test("does not hallucinate unknown protocols", async () => {
  const result = await handleWebhook({
    toolCalls: [
      {
        id: "call_2",
        name: "get_protocol",
        arguments: { task: "unknown orchid pollen isotope capture" }
      }
    ]
  });

  assert.equal(result.results[0].result.status, "not_found");
  assert.match(result.results[0].result.answer, /supervisor/i);
});

test("interprets inertial sensor report with uncertainty", async () => {
  const result = await handleWebhook({
    toolCalls: [
      {
        id: "call_3",
        name: "interpret_sensor_report",
        arguments: {
          sensor: "gyroscope",
          reading: "large rotation spikes during centrifuge run",
          context: "portable centrifuge vibration check"
        }
      }
    ]
  });

  assert.equal(result.results[0].result.status, "ok");
  assert.match(result.results[0].result.confidence, /medium|low/);
  assert.match(result.results[0].result.inferenceBoundary, /not a calibrated instrument/);
});

test("records stage speakerphone noise as noisy confirmation lane", () => {
  clearSignals();
  const event = recordSignal({
    type: "audio",
    label: "stage speakerphone echo and room noise",
    source: "speakerphone",
    intensity: 82,
    riskLevel: "medium"
  });
  const latest = latestSignals();

  assert.equal(event.processingLane, "noisy_confirmation");
  assert.equal(latest.summary.processingLane, "noisy_confirmation");
  assert.match(latest.summary.latestAsk, /alone|worker|radio|powered equipment/i);
});

test("records biohazard cue as emergency priority lane", () => {
  clearSignals();
  const event = recordSignal({
    type: "environment",
    label: "biohazard spill cue",
    source: "caller",
    intensity: 96,
    riskLevel: "high"
  });

  assert.equal(event.processingLane, "emergency_priority");
  assert.equal(latestSignals().summary.latestRisk, "high");
});

test("assesses environment risk through Vapi tool call", async () => {
  const result = await handleWebhook({
    toolCalls: [
      {
        id: "call_4",
        name: "assess_environment_risk",
        arguments: {
          audio: "stage speakerphone echo with radio chatter",
          connectivity: "mobile data down, voice only",
          description: "possible other worker nearby"
        }
      }
    ]
  });

  assert.equal(result.results[0].result.status, "ok");
  assert.equal(result.results[0].result.processingLane, "noisy_confirmation");
  assert.match(result.results[0].result.inferenceBoundary, /cannot identify people/i);
});
