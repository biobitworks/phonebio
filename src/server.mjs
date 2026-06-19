import http from "node:http";
import { createReadStream } from "node:fs";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";
import {
  assessEnvironmentRisk,
  compressObservation,
  getProtocol,
  getSafetySheet,
  interpretSensorReport,
  troubleshootHardware
} from "./knowledge.mjs";

const port = Number(process.env.PORT ?? 3000);
const __dirname = fileURLToPath(new URL(".", import.meta.url));
const publicDir = join(__dirname, "..", "public");

const signalEvents = [];
const maxSignals = 240;

const tools = {
  get_protocol: getProtocol,
  get_safety_sheet: getSafetySheet,
  troubleshoot_hardware: troubleshootHardware,
  interpret_sensor_report: interpretSensorReport,
  compress_observation: async (args) => compressObservation(args),
  assess_environment_risk: async (args) => assessEnvironmentRisk(args)
};

function jsonResponse(response, statusCode, payload) {
  response.writeHead(statusCode, { "content-type": "application/json" });
  response.end(JSON.stringify(payload));
}

function textResponse(response, statusCode, payload, contentType = "text/plain; charset=utf-8") {
  response.writeHead(statusCode, { "content-type": contentType });
  response.end(payload);
}

function contentTypeFor(pathname) {
  const types = {
    ".html": "text/html; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json"
  };
  return types[extname(pathname)] ?? "application/octet-stream";
}

function serveStatic(response, pathname) {
  const requested = pathname === "/dashboard" ? "/dashboard.html" : pathname.replace(/^\/static\//, "/");
  const fullPath = normalize(join(publicDir, requested));
  if (!fullPath.startsWith(publicDir)) {
    jsonResponse(response, 403, { status: "forbidden" });
    return;
  }
  const stream = createReadStream(fullPath);
  stream.on("error", () => jsonResponse(response, 404, { status: "not_found" }));
  response.writeHead(200, { "content-type": contentTypeFor(fullPath) });
  stream.pipe(response);
}

async function readJson(request) {
  const chunks = [];
  for await (const chunk of request) chunks.push(chunk);
  if (chunks.length === 0) return {};
  return JSON.parse(Buffer.concat(chunks).toString("utf8"));
}

function parseToolCalls(payload) {
  const message = payload.message ?? payload;
  return (
    message.toolCalls ??
    message.toolCallList ??
    payload.toolCalls ??
    payload.toolCallList ??
    []
  );
}

function toolName(call) {
  return call.function?.name ?? call.name ?? call.toolName ?? call.type;
}

function toolArgs(call) {
  const args = call.function?.arguments ?? call.arguments ?? call.args ?? {};
  if (typeof args === "string") {
    try {
      return JSON.parse(args);
    } catch {
      return { description: args };
    }
  }
  return args ?? {};
}

export async function handleWebhook(payload) {
  const calls = parseToolCalls(payload);
  if (!Array.isArray(calls) || calls.length === 0) {
    return { status: "ignored", message: "No tool calls found." };
  }

  const results = [];
  for (const call of calls) {
    const name = toolName(call);
    const tool = tools[name];
    const toolCallId = call.id ?? call.toolCallId ?? name ?? "unknown";
    if (!tool) {
      results.push({
        toolCallId,
        result: {
          status: "error",
          answer: `Unsupported tool: ${name}`
        }
      });
      continue;
    }
    results.push({
      toolCallId,
      result: await tool(toolArgs(call))
    });
  }
  return { results };
}

function clamp(value, min = 0, max = 100) {
  const number = Number(value);
  if (!Number.isFinite(number)) return min;
  return Math.min(max, Math.max(min, number));
}

function riskFromSignal(event) {
  const highSignals = ["biohazard", "chemical", "gas", "fire", "smoke", "fall", "exposure"];
  if (event.riskLevel) return event.riskLevel;
  if (highSignals.some((term) => `${event.type} ${event.label}`.toLowerCase().includes(term))) return "high";
  if (event.intensity >= 75) return "medium";
  if (event.intensity >= 45) return "low_to_medium";
  return "low";
}

function recommendedQuestion(event) {
  const haystack = `${event.type} ${event.label} ${event.source}`.toLowerCase();
  if (["voice", "audio", "radio", "ble", "uwb", "device"].some((term) => haystack.includes(term))) {
    return "Are you alone, with another worker, near a radio, or near powered equipment?";
  }
  if (["vibration", "accelerometer", "gyro", "machinery"].some((term) => haystack.includes(term))) {
    return "Is the phone in your hand, pocket, pack, or on the equipment?";
  }
  if (["gps", "location", "barometer", "pressure"].some((term) => haystack.includes(term))) {
    return "Can you confirm the location, accuracy, and units?";
  }
  return "What changed, and what is the most immediate hazard?";
}

function processingLane(event) {
  const haystack = `${event.type} ${event.label} ${event.source} ${event.riskLevel}`.toLowerCase();
  if (event.riskLevel === "high" || ["biohazard", "exposure", "fire", "smoke", "gas", "fall"].some((term) => haystack.includes(term))) {
    return "emergency_priority";
  }
  if (["stage", "speaker", "echo", "voice overlap", "radio", "ble", "uwb", "noise", "machinery"].some((term) => haystack.includes(term))) {
    return "noisy_confirmation";
  }
  if (["vibration", "barometer", "gps", "pressure", "accelerometer"].some((term) => haystack.includes(term))) {
    return "sensor_context";
  }
  return "normal_call";
}

export function recordSignal(input = {}) {
  const event = {
    id: input.id ?? `sig_${Date.now()}_${signalEvents.length}`,
    timestamp: input.timestamp ?? new Date().toISOString(),
    type: String(input.type ?? "sensor"),
    label: String(input.label ?? input.description ?? "Signal event"),
    source: String(input.source ?? "demo"),
    intensity: clamp(input.intensity ?? input.value ?? 0),
    unit: input.unit ? String(input.unit) : "",
    phonePlacement: input.phonePlacement ? String(input.phonePlacement) : "",
    confidence: input.confidence ? String(input.confidence) : "medium",
    riskLevel: String(input.riskLevel ?? ""),
    ask: input.ask ? String(input.ask) : "",
    processingLane: input.processingLane ? String(input.processingLane) : ""
  };
  event.riskLevel = riskFromSignal(event);
  event.ask = event.ask || recommendedQuestion(event);
  event.processingLane = event.processingLane || processingLane(event);
  signalEvents.push(event);
  while (signalEvents.length > maxSignals) signalEvents.shift();
  return event;
}

export function latestSignals() {
  return {
    status: "ok",
    count: signalEvents.length,
    signals: [...signalEvents],
    summary: summarizeSignals(signalEvents)
  };
}

function summarizeSignals(events) {
  const latest = events.at(-1);
  const highCount = events.filter((event) => event.riskLevel === "high").length;
  const mediumCount = events.filter((event) => event.riskLevel === "medium").length;
  return {
    latestRisk: latest?.riskLevel ?? "none",
    latestAsk: latest?.ask ?? "",
    processingLane: latest?.processingLane ?? "idle",
    highCount,
    mediumCount,
    channels: [...new Set(events.map((event) => event.type))].sort()
  };
}

export function clearSignals() {
  signalEvents.length = 0;
}

export function createServer() {
  return http.createServer(async (request, response) => {
    try {
      if (request.method === "GET" && request.url === "/health") {
        jsonResponse(response, 200, { status: "ok", service: "phonebio-vapi-webhook" });
        return;
      }
      if (request.method === "GET" && request.url === "/dashboard") {
        serveStatic(response, "/dashboard");
        return;
      }
      if (request.method === "GET" && ["/", "/dashboard.html", "/dashboard.css", "/dashboard.js"].includes(request.url ?? "")) {
        serveStatic(response, request.url === "/" ? "/dashboard.html" : request.url ?? "/dashboard.html");
        return;
      }
      if (request.method === "GET" && request.url?.startsWith("/static/")) {
        serveStatic(response, request.url);
        return;
      }
      if (request.method === "GET" && request.url === "/signals/latest") {
        jsonResponse(response, 200, latestSignals());
        return;
      }
      if (request.method === "POST" && request.url === "/signals") {
        const payload = await readJson(request);
        jsonResponse(response, 200, { status: "ok", signal: recordSignal(payload) });
        return;
      }
      if (request.method === "POST" && request.url === "/signals/clear") {
        clearSignals();
        jsonResponse(response, 200, { status: "ok" });
        return;
      }
      if (request.method === "POST" && request.url === "/webhook") {
        const payload = await readJson(request);
        jsonResponse(response, 200, await handleWebhook(payload));
        return;
      }
      jsonResponse(response, 404, { status: "not_found" });
    } catch (error) {
      jsonResponse(response, 500, { status: "error", error: error.message });
    }
  });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  createServer().listen(port, () => {
    console.log(`PhoneBio webhook listening on http://localhost:${port}`);
  });
}
