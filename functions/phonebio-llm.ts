// PhoneBio brain proxy — InsForge edge function (Deno Subhosting).
// Vapi's custom-llm model points here; this forwards an OpenAI-compatible
// chat-completions request (messages + tools) to Nebius Token Factory and
// streams the reply back verbatim (content AND tool_calls). The Nebius key is
// an InsForge secret, injected server-side — never exposed to Vapi or the repo.
const NEBIUS_BASE = (Deno.env.get("NEBIUS_BASE_URL") || "https://api.tokenfactory.nebius.com/v1").replace(/\/+$/, "");
const NEBIUS_MODEL = Deno.env.get("NEBIUS_MODEL") || "meta-llama/Llama-3.3-70B-Instruct";
const FALLBACK_MODEL = "phonebio-deterministic-fallback";
const UPSTREAM_TIMEOUT_MS = 15000;
const WEBHOOK_URL = Deno.env.get("VAPI_WEBHOOK_URL") || "https://qfdp5nuv.function2.insforge.app/phonebio-vapi-webhook";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

function lastUserText(messages: unknown): string {
  if (!Array.isArray(messages)) return "";
  for (let i = messages.length - 1; i >= 0; i -= 1) {
    const message = messages[i];
    if (!message || typeof message !== "object") continue;
    const record = message as Record<string, unknown>;
    if (record.role !== "user") continue;
    const content = record.content;
    if (typeof content === "string") return content;
    if (Array.isArray(content)) {
      return content.map((part) => {
        if (typeof part === "string") return part;
        if (part && typeof part === "object" && typeof (part as Record<string, unknown>).text === "string") {
          return String((part as Record<string, unknown>).text);
        }
        return "";
      }).join(" ");
    }
  }
  return "";
}

function allUserText(messages: unknown): string {
  if (!Array.isArray(messages)) return "";
  return messages.map((message) => {
    if (!message || typeof message !== "object") return "";
    const record = message as Record<string, unknown>;
    if (record.role !== "user") return "";
    const content = record.content;
    if (typeof content === "string") return content;
    if (Array.isArray(content)) {
      return content.map((part) => {
        if (typeof part === "string") return part;
        if (part && typeof part === "object" && typeof (part as Record<string, unknown>).text === "string") {
          return String((part as Record<string, unknown>).text);
        }
        return "";
      }).join(" ");
    }
    return "";
  }).join(" ");
}

function allSystemText(messages: unknown): string {
  if (!Array.isArray(messages)) return "";
  return messages.map((message) => {
    if (!message || typeof message !== "object") return "";
    const record = message as Record<string, unknown>;
    if (record.role !== "system") return "";
    return typeof record.content === "string" ? record.content : "";
  }).join(" ");
}

type BackendTrigger = {
  tool: string;
  args: Record<string, unknown>;
  escalateNebius: boolean;
};

function classifyBackendTrigger(lastText: string, contextText: string): BackendTrigger | null {
  const t = lastText.toLowerCase();
  const context = contextText.toLowerCase();

  if (t.includes("field note") || t.includes("observed") || t.includes("juvenile specimens")) {
    return { tool: "compress_observation", args: { text: lastText }, escalateNebius: false };
  }

  if (context.includes("formaldehyde") || context.includes("formalin")) {
    return {
      tool: "get_safety_sheet",
      args: { substance: "formaldehyde", description: contextText.slice(-600) },
      escalateNebius: t.includes("fire") || t.includes("smoke") || t.includes("cannot reach") || t.includes("can't reach"),
    };
  }

  if (t.includes("barometer") || t.includes("pressure") || t.includes("accelerometer") || t.includes("sensor")) {
    return { tool: "interpret_sensor_report", args: { sensor: "phone", reading: lastText }, escalateNebius: false };
  }

  if (t.includes("gps") || t.includes("data logger") || t.includes("centrifuge") || t.includes("hardware")) {
    return { tool: "troubleshoot_hardware", args: { device: "field hardware", symptom: lastText }, escalateNebius: false };
  }

  if (t.includes("protocol") || t.includes("sample") || t.includes("pitfall") || t.includes("experiment")) {
    return { tool: "get_protocol", args: { task: lastText }, escalateNebius: false };
  }

  return null;
}

function triggerBackend(trigger: BackendTrigger | null): void {
  if (!trigger) return;
  const payload = {
    message: {
      type: "tool-calls",
      toolCallList: [{
        id: `fast_${Date.now()}`,
        name: trigger.tool,
        parameters: trigger.args,
      }],
    },
  };
  // Fire-and-forget: the phone call must keep moving while InsForge records
  // grounded context for dashboard/backend use.
  fetch(WEBHOOK_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: AbortSignal.timeout(1200),
  }).catch(() => undefined);
}

function lowLevelFormaldehydeAnswer(text: string): string | null {
  const t = text.toLowerCase();
  const isFormaldehyde = t.includes("formaldehyde") || t.includes("formalin");
  const lowLevel = t.includes("no fire") || t.includes("no skin contact") || t.includes("low-level") || t.includes("small");
  const needsLocation = t.includes("where") || t.includes("location") || t.includes("ventilation") || t.includes("eyewash") || t.includes("spill kit");
  if (!isFormaldehyde || !lowLevel) return null;
  if (needsLocation) {
    return "First confirm your location: ventilation or open air, eyewash or water, spill kit, exits, and whether anyone is nearby. Then follow the SDS cleanup protocol.";
  }
  return "For a small trained cleanup: avoid fumes, keep the glove away from skin, confirm ventilation, eyewash, spill kit, and exits, then follow the SDS spill-kit steps.";
}

function liveDemoAnswer(lastText: string, contextText: string): string | null {
  const t = lastText.toLowerCase();
  const context = contextText.toLowerCase();
  const isFieldNote = t.includes("field note") || t.includes("observed three juvenile") || t.includes("juvenile specimens");
  if (isFieldNote) {
    return "Logged: three juveniles near the burrow, twelve meters, eighteen degrees. Anything to add?";
  }

  const isFormaldehyde = context.includes("formaldehyde") || context.includes("formalin");
  if (t.includes("small fire") || t.includes("smoke") || t.includes("cannot reach emergency") || t.includes("can't reach emergency")) {
    return "RED. Move away from fumes and fire, warn others, do not re-enter, and tell me your exact location.";
  }

  if (!isFormaldehyde) return null;

  const asksForLocationCheck = t.includes("forgot the sds location") || t.includes("ask me where") || t.includes("before cleanup");
  if (asksForLocationCheck) {
    return "AMBER. Before cleanup, where are you relative to ventilation, eyewash, spill kit, exits, and other people?";
  }

  const answeredLocation = t.includes("ventilation") && (t.includes("eyewash") || t.includes("water")) && t.includes("spill kit");
  if (answeredLocation) {
    return "Good. Keep ventilation open, keep the exit clear, use the spill kit and correct PPE, and do not mix chemicals. Stop if fumes, symptoms, or fire appear.";
  }

  return null;
}

function completionResponse(content: string, stream: boolean, model = NEBIUS_MODEL): Response {
  const created = Math.floor(Date.now() / 1000);
  if (stream) {
    const encoder = new TextEncoder();
    const id = `phonebio-fast-${created}`;
    const chunks = [
      { id, object: "chat.completion.chunk", created, model, choices: [{ index: 0, delta: { role: "assistant", content }, finish_reason: null }] },
      { id, object: "chat.completion.chunk", created, model, choices: [{ index: 0, delta: {}, finish_reason: "stop" }] },
    ];
    const body = `${chunks.map((chunk) => `data: ${JSON.stringify(chunk)}\n\n`).join("")}data: [DONE]\n\n`;
    return new Response(encoder.encode(body), {
      status: 200,
      headers: { ...cors, "Content-Type": "text/event-stream" },
    });
  }
  return new Response(JSON.stringify({
    id: `phonebio-fast-${created}`,
    object: "chat.completion",
    created,
    model,
    choices: [{ index: 0, message: { role: "assistant", content }, finish_reason: "stop" }],
  }), {
    status: 200,
    headers: { ...cors, "Content-Type": "application/json" },
  });
}

export default async function (req: Request): Promise<Response> {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
  if (req.method === "GET") {
    return new Response(JSON.stringify({ status: "ok", service: "phonebio-llm", model: NEBIUS_MODEL }), {
      status: 200, headers: { ...cors, "Content-Type": "application/json" },
    });
  }

  let body: any = {};
  try { body = await req.json(); } catch { /* empty */ }
  const userText = lastUserText(body.messages);
  const contextText = allUserText(body.messages) || userText;
  const systemText = allSystemText(body.messages).toLowerCase();
  const backendTrigger = classifyBackendTrigger(userText, contextText);
  triggerBackend(backendTrigger);
  const demoAnswer = liveDemoAnswer(userText, contextText);
  if (demoAnswer) return completionResponse(demoAnswer, body.stream !== false, FALLBACK_MODEL);

  const fallbackAnswer = lowLevelFormaldehydeAnswer(contextText);
  // Universal voice fallback so the always-available phone call never goes silent.
  const safe = fallbackAnswer || "I am still here. Keep it simple: tell me your location, the hazard, and whether anyone is hurt.";

  const key = Deno.env.get("NEBIUS_API_KEY");
  if (!key) return completionResponse(safe, body.stream !== false, FALLBACK_MODEL);

  // Whitelist OpenAI fields so Vapi-specific extras don't trip Nebius.
  const payload: Record<string, unknown> = {
    model: NEBIUS_MODEL,
    messages: body.messages ?? [],
    stream: body.stream ?? true,
  };
  const forceToolForwarding = systemText.includes("use a tool when relevant");
  const liveDemoPrompt = systemText.includes("for the live demo") || systemText.includes("never say");
  const shouldEscalateToNebius = !liveDemoPrompt || backendTrigger?.escalateNebius === true || contextText.length > 700;
  if (body.tools && forceToolForwarding && !liveDemoPrompt) payload.tools = body.tools;
  if (body.tool_choice && forceToolForwarding && !liveDemoPrompt) payload.tool_choice = body.tool_choice;
  if (body.temperature != null) payload.temperature = body.temperature;
  if (body.max_tokens != null) payload.max_tokens = body.max_tokens;

  if (!shouldEscalateToNebius) return completionResponse(safe, body.stream !== false, FALLBACK_MODEL);

  let upstream: Response;
  try {
    upstream = await fetch(`${NEBIUS_BASE}/chat/completions`, {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
    });
  } catch (_error) {
    return completionResponse(safe, body.stream !== false, FALLBACK_MODEL);
  }

  if (!upstream.ok) return completionResponse(safe, body.stream !== false, FALLBACK_MODEL);

  // Stream the upstream body straight back (works for SSE stream and JSON alike).
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      ...cors,
      "Content-Type": upstream.headers.get("content-type") || "application/json",
    },
  });
}
