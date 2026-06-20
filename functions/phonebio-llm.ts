// PhoneBio brain proxy - InsForge edge function (Deno Subhosting).
//
// Vapi's custom-llm model points here. This function forwards an
// OpenAI-compatible chat-completions request to Nebius Token Factory and returns
// the upstream response verbatim, including tool_calls. Do not gate tool
// forwarding on prompt magic strings; Vapi/Nebius need the real tool schema on
// every relevant call.
const NEBIUS_BASE = (Deno.env.get("NEBIUS_BASE_URL") || "https://api.tokenfactory.nebius.com/v1").replace(/\/+$/, "");
const NEBIUS_MODEL = Deno.env.get("NEBIUS_MODEL") || "Qwen/Qwen3-30B-A3B-Instruct-2507";
const NEBIUS_HEAVY_MODEL = Deno.env.get("NEBIUS_HEAVY_MODEL") || "meta-llama/Llama-3.3-70B-Instruct";
const FALLBACK_MODEL = "phonebio-deterministic-fallback";
const UPSTREAM_TIMEOUT_MS = 20000;

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

function fallbackResponse(reason: string, stream: boolean): Response {
  const created = Math.floor(Date.now() / 1000);
  const content = "I hit a backend delay. Stop work if there is danger, move to a safe location, and tell me the hazard and whether anyone is hurt.";
  if (stream) {
    const id = `phonebio-fallback-${created}`;
    const chunks = [
      { id, object: "chat.completion.chunk", created, model: FALLBACK_MODEL, choices: [{ index: 0, delta: { role: "assistant", content }, finish_reason: null }] },
      { id, object: "chat.completion.chunk", created, model: FALLBACK_MODEL, choices: [{ index: 0, delta: {}, finish_reason: "stop" }] },
    ];
    const body = `${chunks.map((chunk) => `data: ${JSON.stringify(chunk)}\n\n`).join("")}data: [DONE]\n\n`;
    return new Response(body, {
      status: 200,
      headers: { ...cors, "Content-Type": "text/event-stream", "X-PhoneBio-Fallback": reason },
    });
  }
  return new Response(JSON.stringify({
    id: `phonebio-fallback-${created}`,
    object: "chat.completion",
    created,
    model: FALLBACK_MODEL,
    choices: [{ index: 0, message: { role: "assistant", content }, finish_reason: "stop" }],
  }), {
    status: 200,
    headers: { ...cors, "Content-Type": "application/json", "X-PhoneBio-Fallback": reason },
  });
}

function copyIfPresent(source: Record<string, unknown>, target: Record<string, unknown>, key: string): void {
  if (source[key] !== undefined) target[key] = source[key];
}

function buildPayload(body: Record<string, unknown>): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    model: NEBIUS_MODEL,
    messages: Array.isArray(body.messages) ? body.messages : [],
    stream: body.stream ?? true,
  };

  // These are the OpenAI-compatible fields Vapi may send. Tools are always
  // forwarded when present so Nebius can emit real tool_calls.
  for (const key of [
    "tools",
    "tool_choice",
    "temperature",
    "max_tokens",
    "top_p",
    "frequency_penalty",
    "presence_penalty",
    "response_format",
    "seed",
    "stop",
    "user",
  ]) {
    copyIfPresent(body, payload, key);
  }
  return payload;
}

export default async function (req: Request): Promise<Response> {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
  if (req.method === "GET") {
    return new Response(JSON.stringify({
      status: "ok",
      service: "phonebio-llm",
      model: NEBIUS_MODEL,
      heavyModel: NEBIUS_HEAVY_MODEL,
      toolForwarding: "always",
      fallbackPolicy: "upstream-error-only",
    }), {
      status: 200,
      headers: { ...cors, "Content-Type": "application/json" },
    });
  }

  let body: Record<string, unknown> = {};
  try {
    body = await req.json();
  } catch {
    return fallbackResponse("bad-json", false);
  }

  const key = Deno.env.get("NEBIUS_API_KEY");
  if (!key) return fallbackResponse("missing-nebius-key", body.stream !== false);

  let upstream: Response;
  try {
    upstream = await fetch(`${NEBIUS_BASE}/chat/completions`, {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify(buildPayload(body)),
      signal: AbortSignal.timeout(UPSTREAM_TIMEOUT_MS),
    });
  } catch (_error) {
    return fallbackResponse("upstream-timeout-or-network", body.stream !== false);
  }

  if (!upstream.ok) return fallbackResponse(`upstream-${upstream.status}`, body.stream !== false);

  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      ...cors,
      "Content-Type": upstream.headers.get("content-type") || "application/json",
    },
  });
}
