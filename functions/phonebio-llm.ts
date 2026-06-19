// PhoneBio brain proxy — InsForge edge function (Deno Subhosting).
// Vapi's custom-llm model points here; this forwards an OpenAI-compatible
// chat-completions request (messages + tools) to Nebius Token Factory and
// streams the reply back verbatim (content AND tool_calls). The Nebius key is
// an InsForge secret, injected server-side — never exposed to Vapi or the repo.
const NEBIUS_BASE = (Deno.env.get("NEBIUS_BASE_URL") || "https://api.tokenfactory.nebius.com/v1").replace(/\/+$/, "");
const NEBIUS_MODEL = Deno.env.get("NEBIUS_MODEL") || "meta-llama/Llama-3.3-70B-Instruct";
const FALLBACK_MODEL = "phonebio-deterministic-fallback";

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
  const fallbackAnswer = lowLevelFormaldehydeAnswer(lastUserText(body.messages));

  const key = Deno.env.get("NEBIUS_API_KEY");
  if (!key) {
    if (fallbackAnswer) return completionResponse(fallbackAnswer, body.stream !== false, FALLBACK_MODEL);
    return new Response(JSON.stringify({ error: "NEBIUS_API_KEY secret not set" }), {
      status: 500, headers: { ...cors, "Content-Type": "application/json" },
    });
  }

  // Whitelist OpenAI fields so Vapi-specific extras don't trip Nebius.
  const payload: Record<string, unknown> = {
    model: NEBIUS_MODEL,
    messages: body.messages ?? [],
    stream: body.stream ?? true,
  };
  if (body.tools) payload.tools = body.tools;
  if (body.tool_choice) payload.tool_choice = body.tool_choice;
  if (body.temperature != null) payload.temperature = body.temperature;
  if (body.max_tokens != null) payload.max_tokens = body.max_tokens;

  let upstream: Response;
  try {
    upstream = await fetch(`${NEBIUS_BASE}/chat/completions`, {
      method: "POST",
      headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(8000),
    });
  } catch (_error) {
    if (fallbackAnswer) return completionResponse(fallbackAnswer, body.stream !== false, FALLBACK_MODEL);
    throw _error;
  }

  if (!upstream.ok && fallbackAnswer) return completionResponse(fallbackAnswer, body.stream !== false, FALLBACK_MODEL);

  // Stream the upstream body straight back (works for SSE stream and JSON alike).
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      ...cors,
      "Content-Type": upstream.headers.get("content-type") || "application/json",
    },
  });
}
