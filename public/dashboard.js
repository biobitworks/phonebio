const chart = document.querySelector("#signalChart");
const ctx = chart.getContext("2d");
const eventLog = document.querySelector("#eventLog");
const askLine = document.querySelector("#askLine");
const riskState = document.querySelector("#riskState");
const currentRisk = document.querySelector("#currentRisk");
const laneState = document.querySelector("#laneState");
const processingLane = document.querySelector("#processingLane");
const eventCount = document.querySelector("#eventCount");
const connectionState = document.querySelector("#connectionState");
const orchestratorState = document.querySelector("#orchestratorState");
const orchestratorDecision = document.querySelector("#orchestratorDecision");
const resourceRoute = document.querySelector("#resourceRoute");
const sensorBasis = document.querySelector("#sensorBasis");

const colors = {
  audio: "#55c7ff",
  motion: "#ffcf5a",
  wireless: "#7ee083",
  environment: "#ff7b7b",
  location: "#cfa2ff",
  default: "#d8e6d8"
};

const demos = {
  voice: { type: "audio", label: "possible voice overlap", intensity: 72, source: "microphone", riskLevel: "medium" },
  stage: { type: "audio", label: "stage speakerphone echo and room noise", intensity: 82, source: "speakerphone", riskLevel: "medium" },
  radio: { type: "wireless", label: "radio or BLE device nearby", intensity: 64, source: "BLE/radio", riskLevel: "low_to_medium" },
  vibration: { type: "motion", label: "centrifuge vibration spike", intensity: 88, source: "accelerometer", riskLevel: "medium" },
  barometer: { type: "environment", label: "pressure drop trend", intensity: 56, source: "barometer", riskLevel: "low_to_medium" },
  gps: { type: "location", label: "GPS accuracy degraded", intensity: 48, source: "GNSS", riskLevel: "low_to_medium" },
  executorch: { type: "environment", label: "ExecuTorch local sensor gate", intensity: 38, source: "on-device .pte", riskLevel: "low", processingLane: "sensor_context" },
  biohazard: { type: "environment", label: "biohazard spill cue", intensity: 96, source: "caller", riskLevel: "high" }
};

const localSignals = [];
const apiEnabled = ["localhost", "127.0.0.1"].includes(window.location.hostname) || window.location.search.includes("api=1");

function clamp(value, min = 0, max = 100) {
  const number = Number(value);
  if (!Number.isFinite(number)) return min;
  return Math.min(max, Math.max(min, number));
}

function fallbackQuestion(signal) {
  const text = `${signal.type} ${signal.label} ${signal.source}`.toLowerCase();
  if (["voice", "audio", "radio", "ble", "uwb", "device", "speaker"].some((term) => text.includes(term))) {
    return "Are you alone, with another worker, near a radio, or near powered equipment?";
  }
  if (["vibration", "accelerometer", "gyro", "machinery"].some((term) => text.includes(term))) {
    return "Is the phone in your hand, pocket, pack, or on the equipment?";
  }
  if (["gps", "location", "barometer", "pressure"].some((term) => text.includes(term))) {
    return "Can you confirm the location, accuracy, and units?";
  }
  return "What changed, and what is the most immediate hazard?";
}

function fallbackLane(signal) {
  const text = `${signal.type} ${signal.label} ${signal.source} ${signal.riskLevel}`.toLowerCase();
  if (signal.riskLevel === "high" || ["biohazard", "exposure", "fire", "smoke", "gas", "fall"].some((term) => text.includes(term))) {
    return "emergency_priority";
  }
  if (["stage", "speaker", "echo", "voice overlap", "radio", "ble", "uwb", "noise", "machinery"].some((term) => text.includes(term))) {
    return "noisy_confirmation";
  }
  if (["vibration", "barometer", "gps", "pressure", "accelerometer"].some((term) => text.includes(term))) {
    return "sensor_context";
  }
  return "normal_call";
}

function fallbackPayload() {
  const latestSignal = localSignals.at(-1);
  const orchestration = orchestrate(latestSignal);
  return {
    status: "ok",
    count: localSignals.length,
    signals: localSignals,
    summary: {
      latestRisk: latestSignal?.riskLevel ?? "none",
      latestAsk: latestSignal?.ask ?? "",
      processingLane: latestSignal?.processingLane ?? "idle",
      orchestration,
      highCount: localSignals.filter((signal) => signal.riskLevel === "high").length,
      mediumCount: localSignals.filter((signal) => signal.riskLevel === "medium").length,
      channels: [...new Set(localSignals.map((signal) => signal.type))].sort()
    }
  };
}

function orchestrate(signal) {
  if (!signal) {
    return {
      decision: "standby",
      resourceRoute: "local only",
      sensorBasis: "none"
    };
  }
  if (signal.processingLane === "emergency_priority") {
    return {
      decision: "short safety action",
      resourceRoute: "Vapi + InsForge priority",
      sensorBasis: `${signal.type} / ${signal.source}`
    };
  }
  if (signal.processingLane === "noisy_confirmation") {
    return {
      decision: "ask confirmation",
      resourceRoute: "ExecuTorch filter, then Vapi",
      sensorBasis: `${signal.type} / ${signal.source}`
    };
  }
  if (signal.processingLane === "sensor_context") {
    return {
      decision: "summarize context",
      resourceRoute: "ExecuTorch local .pte",
      sensorBasis: `${signal.type} / ${signal.source}`
    };
  }
  return {
    decision: "answer normally",
    resourceRoute: "local cache + Vapi",
    sensorBasis: `${signal.type} / ${signal.source}`
  };
}

function recordLocal(signal) {
  const event = {
    id: `local_${Date.now()}_${localSignals.length}`,
    timestamp: new Date().toISOString(),
    type: String(signal.type ?? "sensor"),
    label: String(signal.label ?? "Signal event"),
    source: String(signal.source ?? "static-demo"),
    intensity: clamp(signal.intensity ?? signal.value ?? 0),
    unit: signal.unit ? String(signal.unit) : "",
    riskLevel: String(signal.riskLevel ?? "low"),
    ask: signal.ask ? String(signal.ask) : "",
    processingLane: signal.processingLane ? String(signal.processingLane) : ""
  };
  event.ask = event.ask || fallbackQuestion(event);
  event.processingLane = event.processingLane || fallbackLane(event);
  localSignals.push(event);
  while (localSignals.length > 240) localSignals.shift();
  return event;
}

async function postSignal(signal) {
  if (!apiEnabled) {
    recordLocal(signal);
    connectionState.textContent = "Static demo";
    return { status: "ok", signal };
  }
  try {
    const response = await fetch("/signals", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(signal)
    });
    if (!response.ok) throw new Error(`signal post failed: ${response.status}`);
    connectionState.textContent = "Local API";
    return response.json();
  } catch {
    recordLocal(signal);
    connectionState.textContent = "Static demo";
    return { status: "ok", signal };
  }
}

async function latest() {
  if (!apiEnabled) {
    connectionState.textContent = "Static demo";
    return fallbackPayload();
  }
  try {
    const response = await fetch("/signals/latest");
    if (!response.ok) throw new Error(`latest failed: ${response.status}`);
    connectionState.textContent = "Local API";
    return response.json();
  } catch {
    connectionState.textContent = "Static demo";
    return fallbackPayload();
  }
}

function draw(signals) {
  const width = chart.width;
  const height = chart.height;
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#202720";
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = "#334033";
  ctx.lineWidth = 1;
  for (let y = 40; y < height; y += 40) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }
  const slice = signals.slice(-40);
  const step = width / Math.max(slice.length, 1);
  slice.forEach((signal, index) => {
    const x = index * step + step * 0.5;
    const spikeHeight = (Number(signal.intensity) / 100) * (height - 26);
    const y = height - spikeHeight;
    ctx.strokeStyle = colors[signal.type] ?? colors.default;
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo(x, height - 10);
    ctx.lineTo(x, y);
    ctx.stroke();
    ctx.fillStyle = ctx.strokeStyle;
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fill();
  });
}

function render(payload) {
  const signals = payload.signals ?? [];
  draw(signals);
  eventCount.textContent = `${signals.length} signals`;
  const risk = payload.summary?.latestRisk ?? "none";
  const lane = payload.summary?.processingLane ?? "idle";
  const orchestration = payload.summary?.orchestration ?? orchestrate(signals.at(-1));
  riskState.textContent = `risk: ${risk}`;
  laneState.textContent = `lane: ${lane}`;
  orchestratorState.textContent = `orchestrator: ${orchestration.decision}`;
  currentRisk.textContent = risk;
  processingLane.textContent = lane;
  orchestratorDecision.textContent = orchestration.decision;
  resourceRoute.textContent = orchestration.resourceRoute;
  sensorBasis.textContent = orchestration.sensorBasis;
  askLine.textContent = payload.summary?.latestAsk || "Waiting for signal context.";
  eventLog.replaceChildren(
    ...signals.slice(-9).reverse().map((signal) => {
      const item = document.createElement("li");
      const time = new Date(signal.timestamp).toLocaleTimeString();
      item.innerHTML = `<strong>${signal.label}</strong><small>${time} · ${signal.type} · ${signal.intensity}${signal.unit || ""}<br>${signal.processingLane}<br>${signal.ask}</small>`;
      return item;
    })
  );
}

async function refresh() {
  try {
    render(await latest());
  } catch {
    connectionState.textContent = "Static demo";
    render(fallbackPayload());
  }
}

document.querySelectorAll("[data-demo]").forEach((button) => {
  button.addEventListener("click", async () => {
    await postSignal(demos[button.dataset.demo]);
    await refresh();
  });
});

document.querySelector("#clear").addEventListener("click", async () => {
  localSignals.length = 0;
  if (!apiEnabled) {
    connectionState.textContent = "Static demo";
    await refresh();
    return;
  }
  try {
    await fetch("/signals/clear", { method: "POST" });
  } catch {
    connectionState.textContent = "Static demo";
  }
  await refresh();
});

let simTimer;
document.querySelector("#simulate").addEventListener("click", () => {
  if (simTimer) {
    clearInterval(simTimer);
    simTimer = null;
    return;
  }
  const sequence = ["voice", "stage", "radio", "vibration", "barometer", "gps", "executorch", "biohazard"];
  let index = 0;
  simTimer = setInterval(async () => {
    const key = sequence[index % sequence.length];
    const base = demos[key];
    await postSignal({ ...base, intensity: Math.min(100, base.intensity + Math.round(Math.random() * 12 - 4)) });
    await refresh();
    index += 1;
  }, 1100);
});

refresh();
setInterval(refresh, 2500);
