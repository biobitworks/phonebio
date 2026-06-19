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
const captureState = document.querySelector("#captureState");
const armSensorsButton = document.querySelector("#armSensors");
const sensorLines = document.querySelector("#sensorLines");

const CAPTURE_ENDPOINT = "https://qfdp5nuv.function2.insforge.app/phonebio-vapi-webhook";
const sensorSessionId = globalThis.crypto?.randomUUID?.() ?? `demo_${Date.now()}`;
const liveSensor = {
  armed: false,
  lastLoudnessDbfs: null,
  lastMotionMps2: null,
  lastLocationAccuracyMeters: null,
  motionBase: 9.8,
  lastTier: "unknown",
  captureCount: 0
};

const colors = {
  audio: "#55c7ff",
  motion: "#ffcf5a",
  wireless: "#7ee083",
  environment: "#ff7b7b",
  location: "#cfa2ff",
  default: "#d8e6d8"
};

const sensorChannels = ["audio", "motion", "wireless", "environment", "location"];
const channelMeta = {
  audio: {
    label: "Audio",
    unit: "dBFS",
    bandwidth: "high raw / low feature",
    processing: "VAD local, Vapi/Nebius if speech or emergency"
  },
  motion: {
    label: "Motion",
    unit: "m/s2",
    bandwidth: "low",
    processing: "local quantized gate"
  },
  wireless: {
    label: "Wireless",
    unit: "proximity",
    bandwidth: "very low",
    processing: "local context, ask confirmation"
  },
  environment: {
    label: "Environment",
    unit: "trend",
    bandwidth: "very low",
    processing: "local risk matrix, public alert context"
  },
  location: {
    label: "Location",
    unit: "accuracy",
    bandwidth: "low / sensitive",
    processing: "redacted relay only"
  }
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
const remoteCaptureIds = new Set();
const apiEnabled = window.location.search.includes("api=1");

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

function riskTierFromLiveSensors(loudnessDbfs, motionMps2) {
  const loud = Number.isFinite(loudnessDbfs) ? loudnessDbfs : -90;
  const motion = Number.isFinite(motionMps2) ? motionMps2 : 0;
  if (motion >= 6 || (motion >= 3 && loud >= -18)) return "high";
  if (motion >= 2.2 || loud >= -24) return "medium";
  if (motion >= 0.8 || loud >= -38) return "low_to_medium";
  return "low";
}

function liveSignalFromSnapshot() {
  const loud = liveSensor.lastLoudnessDbfs;
  const motion = liveSensor.lastMotionMps2;
  const loudIntensity = Number.isFinite(loud) ? clamp((loud + 65) * 1.8) : 0;
  const motionIntensity = Number.isFinite(motion) ? clamp(motion * 18) : 0;
  const intensity = Math.max(loudIntensity, motionIntensity);
  const tier = riskTierFromLiveSensors(loud, motion);
  liveSensor.lastTier = tier;
  const type = motionIntensity >= loudIntensity ? "motion" : "audio";
  return {
    type,
    label: "live phone sensor packet",
    source: "phone mic + motion",
    intensity,
    unit: "%",
    riskLevel: tier,
    ask: tier === "high"
      ? "Confirm hazard, injuries, location, and whether you can move away safely."
      : "Confirm whether this is speech, machinery, movement, or nearby equipment.",
    processingLane: tier === "high" ? "emergency_priority" : (tier === "medium" ? "noisy_confirmation" : "sensor_context")
  };
}

function liveSignalsFromSnapshot() {
  const loud = liveSensor.lastLoudnessDbfs;
  const motion = liveSensor.lastMotionMps2;
  const locationAccuracy = liveSensor.lastLocationAccuracyMeters;
  const loudIntensity = Number.isFinite(loud) ? clamp((loud + 65) * 1.8) : 0;
  const motionIntensity = Number.isFinite(motion) ? clamp(motion * 18) : 0;
  const locationIntensity = Number.isFinite(locationAccuracy) ? clamp(100 - locationAccuracy) : 0;
  const tier = riskTierFromLiveSensors(loud, motion);
  liveSensor.lastTier = tier;
  const lane = tier === "high" ? "emergency_priority" : (tier === "medium" ? "noisy_confirmation" : "sensor_context");
  const ask = tier === "high"
    ? "Confirm hazard, injuries, location, and whether you can move away safely."
    : "Confirm whether this is speech, machinery, movement, or nearby equipment.";
  const signals = [
    {
      type: "audio",
      label: "live audio level",
      source: "phone microphone feature",
      intensity: loudIntensity,
      value: loud,
      unit: " dBFS",
      riskLevel: tier,
      ask,
      processingLane: loudIntensity >= 65 ? "noisy_confirmation" : lane
    },
    {
      type: "motion",
      label: "live motion delta",
      source: "accelerometer feature",
      intensity: motionIntensity,
      value: motion,
      unit: " m/s2",
      riskLevel: tier,
      ask,
      processingLane: motionIntensity >= 65 ? "emergency_priority" : lane
    }
  ];
  if (Number.isFinite(locationAccuracy)) {
    signals.push({
      type: "location",
      label: "live location accuracy",
      source: "geolocation accuracy only",
      intensity: locationIntensity,
      value: Math.round(locationAccuracy),
      unit: " m",
      riskLevel: tier,
      ask,
      processingLane: "sensor_context"
    });
  }
  return signals;
}

function signalFromCapture(capture) {
  const loud = Number(capture.loudnessDbfs);
  const motion = Number(capture.motionMps2);
  const loudIntensity = Number.isFinite(loud) ? clamp((loud + 65) * 1.8) : 0;
  const motionIntensity = Number.isFinite(motion) ? clamp(motion * 18) : 0;
  const tier = String(capture.riskTier || riskTierFromLiveSensors(loud, motion));
  return {
    id: `remote_${capture.id}`,
    timestamp: capture.receivedAt || new Date().toISOString(),
    type: motionIntensity >= loudIntensity ? "motion" : "audio",
    label: "remote phone sensor capture",
    source: capture.source || "edge capture",
    intensity: Math.max(loudIntensity, motionIntensity),
    unit: "%",
    riskLevel: tier,
    ask: tier === "high"
      ? "Confirm hazard, injuries, location, and whether you can move away safely."
      : "Confirm whether this is speech, machinery, movement, or nearby equipment.",
    processingLane: tier === "high" ? "emergency_priority" : (tier === "medium" ? "noisy_confirmation" : "sensor_context")
  };
}

function signalsFromCapture(capture) {
  const loud = Number(capture.loudnessDbfs);
  const motion = Number(capture.motionMps2);
  const environment = Number(capture.environmentScore);
  const locationAccuracy = Number(capture.locationAccuracyMeters);
  const wireless = Number(capture.wirelessScore);
  const tier = String(capture.riskTier || riskTierFromLiveSensors(loud, motion));
  const base = {
    timestamp: capture.receivedAt || new Date().toISOString(),
    riskLevel: tier,
    ask: tier === "high"
      ? "Confirm hazard, injuries, location, and whether you can move away safely."
      : "Confirm whether this is speech, machinery, movement, or nearby equipment."
  };
  const signals = [
    {
      ...base,
      id: `remote_audio_${capture.id}`,
      type: "audio",
      label: "remote audio level",
      source: capture.source || "edge capture",
      intensity: Number.isFinite(loud) ? clamp((loud + 65) * 1.8) : 0,
      value: Number.isFinite(loud) ? loud : null,
      unit: " dBFS",
      processingLane: "noisy_confirmation"
    },
    {
      ...base,
      id: `remote_motion_${capture.id}`,
      type: "motion",
      label: "remote motion delta",
      source: capture.source || "edge capture",
      intensity: Number.isFinite(motion) ? clamp(motion * 18) : 0,
      value: Number.isFinite(motion) ? motion : null,
      unit: " m/s2",
      processingLane: tier === "high" ? "emergency_priority" : "sensor_context"
    }
  ];
  if (Number.isFinite(wireless)) {
    signals.push({
      ...base,
      id: `remote_wireless_${capture.id}`,
      type: "wireless",
      label: "remote nearby-device score",
      source: capture.source || "edge capture",
      intensity: clamp(wireless),
      value: Math.round(wireless),
      unit: "%",
      processingLane: "noisy_confirmation"
    });
  }
  if (Number.isFinite(environment)) {
    signals.push({
      ...base,
      id: `remote_environment_${capture.id}`,
      type: "environment",
      label: "remote environment score",
      source: capture.source || "edge capture",
      intensity: clamp(environment),
      value: Math.round(environment),
      unit: "%",
      processingLane: tier === "high" ? "emergency_priority" : "sensor_context"
    });
  }
  if (Number.isFinite(locationAccuracy)) {
    signals.push({
      ...base,
      id: `remote_location_${capture.id}`,
      type: "location",
      label: "remote location accuracy",
      source: capture.source || "edge capture",
      intensity: clamp(100 - locationAccuracy),
      value: Math.round(locationAccuracy),
      unit: " m",
      processingLane: "sensor_context"
    });
  }
  return signals;
}

async function captureSnapshot(signal) {
  try {
    const response = await fetch(CAPTURE_ENDPOINT, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({
        type: "sensor-capture",
        snapshot: {
          sessionId: sensorSessionId,
          clientTime: new Date().toISOString(),
          source: "dashboard-web",
          mode: "live-phone-sensors",
          loudnessDbfs: liveSensor.lastLoudnessDbfs,
          motionMps2: liveSensor.lastMotionMps2,
          speakerEstimate: null,
          locationAccuracyMeters: liveSensor.lastLocationAccuracyMeters,
          riskTier: signal.riskLevel
        }
      })
    });
    if (!response.ok) throw new Error(`capture failed: ${response.status}`);
    const body = await response.json();
    liveSensor.captureCount = body.count ?? liveSensor.captureCount + 1;
    captureState.textContent = `capture: ${liveSensor.captureCount} sent`;
  } catch {
    captureState.textContent = "capture: local only";
  }
}

async function pollCaptureFeed() {
  if (liveSensor.armed) return;
  try {
    const response = await fetch(`${CAPTURE_ENDPOINT}?capture=latest`, { cache: "no-store" });
    if (!response.ok) throw new Error(`capture feed failed: ${response.status}`);
    const body = await response.json();
    for (const capture of body.captures || []) {
      if (!capture?.id || remoteCaptureIds.has(capture.id) || capture.sessionId === sensorSessionId) continue;
      remoteCaptureIds.add(capture.id);
      for (const signal of signalsFromCapture(capture)) recordLocal(signal);
    }
    if ((body.count ?? 0) > 0) captureState.textContent = `capture: ${body.count} remote`;
  } catch {
    if (!liveSensor.armed) captureState.textContent = "capture: local only";
  }
}

async function startAudioLevelCapture() {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  const audioContext = new AudioCtx();
  const analyser = audioContext.createAnalyser();
  analyser.fftSize = 512;
  audioContext.createMediaStreamSource(stream).connect(analyser);
  const samples = new Uint8Array(analyser.fftSize);
  const loop = () => {
    analyser.getByteTimeDomainData(samples);
    let sum = 0;
    for (const value of samples) {
      const normalized = (value - 128) / 128;
      sum += normalized * normalized;
    }
    liveSensor.lastLoudnessDbfs = Math.round(20 * Math.log10(Math.sqrt(sum / samples.length) + 1e-7));
    if (liveSensor.armed) requestAnimationFrame(loop);
  };
  loop();
}

async function armLiveSensors() {
  if (liveSensor.armed) {
    captureState.textContent = "capture: already armed";
    return;
  }
  armSensorsButton.disabled = true;
  captureState.textContent = "capture: requesting permissions";
  try {
    if (typeof DeviceMotionEvent?.requestPermission === "function") await DeviceMotionEvent.requestPermission();
    if (typeof DeviceOrientationEvent?.requestPermission === "function") await DeviceOrientationEvent.requestPermission();
  } catch {
    // iOS may deny or skip individual sensor prompts; continue with any channel available.
  }
  window.addEventListener("devicemotion", (event) => {
    const a = event.accelerationIncludingGravity || {};
    const magnitude = Math.hypot(a.x || 0, a.y || 0, a.z || 0);
    liveSensor.motionBase = liveSensor.motionBase * 0.98 + magnitude * 0.02;
    liveSensor.lastMotionMps2 = Math.round(Math.abs(magnitude - liveSensor.motionBase) * 100) / 100;
  });
  try {
    await startAudioLevelCapture();
  } catch {
    liveSensor.lastLoudnessDbfs = null;
  }
  if (navigator.geolocation) {
    navigator.geolocation.watchPosition(
      (position) => {
        liveSensor.lastLocationAccuracyMeters = Math.round(position.coords.accuracy);
      },
      () => {
        liveSensor.lastLocationAccuracyMeters = null;
      },
      { enableHighAccuracy: false, maximumAge: 10000, timeout: 8000 }
    );
  }
  liveSensor.armed = true;
  armSensorsButton.textContent = "Live sensors armed";
  captureState.textContent = "capture: armed";
  setInterval(async () => {
    if (!liveSensor.armed) return;
    const signals = liveSignalsFromSnapshot();
    for (const signal of signals) await postSignal(signal);
    await captureSnapshot(signals.at(-1));
    await refresh();
  }, 1000);
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
    value: signal.value ?? "",
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
  for (let y = 32; y < height; y += 32) {
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }
  sensorChannels.forEach((channel, channelIndex) => {
    const channelSignals = signals.filter((signal) => signal.type === channel).slice(-50);
    const color = colors[channel] ?? colors.default;
    const baseline = height - 22 - channelIndex * 54;
    ctx.strokeStyle = "rgba(238,245,238,.16)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(0, baseline);
    ctx.lineTo(width, baseline);
    ctx.stroke();
    ctx.fillStyle = color;
    ctx.font = "11px ui-monospace, Menlo, monospace";
    ctx.fillText(channelMeta[channel].label, 8, baseline - 30);
    if (channelSignals.length === 0) return;
    const step = width / Math.max(channelSignals.length - 1, 1);
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.beginPath();
    channelSignals.forEach((signal, index) => {
      const x = index * step;
      const y = baseline - (clamp(signal.intensity) / 100) * 42;
      if (index === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();
    const latest = channelSignals.at(-1);
    const x = (channelSignals.length - 1) * step;
    const y = baseline - (clamp(latest.intensity) / 100) * 42;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fill();
  });
}

function latestByChannel(signals) {
  const latest = {};
  for (const signal of signals) {
    if (sensorChannels.includes(signal.type)) latest[signal.type] = signal;
  }
  return latest;
}

function displayValue(channel, signal) {
  if (!signal) return "--";
  if (signal.value !== undefined && signal.value !== null && signal.value !== "") {
    return `${signal.value}${signal.unit || ""}`;
  }
  return `${Math.round(clamp(signal.intensity))}%`;
}

function renderSensorLines(signals) {
  const latest = latestByChannel(signals);
  sensorLines.replaceChildren(
    ...sensorChannels.map((channel) => {
      const meta = channelMeta[channel];
      const signal = latest[channel];
      const item = document.createElement("div");
      item.className = "sensor-line";
      item.style.borderLeftColor = colors[channel] ?? colors.default;
      item.innerHTML = `<strong>${meta.label}</strong>
        <span class="value">${displayValue(channel, signal)}</span>
        <span>${signal?.source || "waiting"} · ${signal?.processingLane || "idle"}</span>
        <span>${meta.bandwidth}</span>
        <span>${meta.processing}</span>`;
      return item;
    })
  );
}

function render(payload) {
  const signals = payload.signals ?? [];
  draw(signals);
  renderSensorLines(signals);
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
      item.innerHTML = `<strong>${signal.label}</strong><small>${time} · ${signal.type} · ${displayValue(signal.type, signal)}<br>${signal.processingLane}<br>${signal.ask}</small>`;
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

armSensorsButton.addEventListener("click", armLiveSensors);

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
setInterval(async () => {
  await pollCaptureFeed();
  await refresh();
}, 1500);
