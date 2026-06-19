// PhoneBio brain proxy — InsForge edge function (Deno Subhosting).
// Vapi's custom-llm model points here; this forwards an OpenAI-compatible
// chat-completions request (messages + tools) to Nebius Token Factory and
// streams the reply back verbatim (content AND tool_calls). The Nebius key is
// an InsForge secret, injected server-side — never exposed to Vapi or the repo.
const NEBIUS_BASE = (Deno.env.get("NEBIUS_BASE_URL") || "https://api.tokenfactory.nebius.com/v1").replace(/\/+$/, "");
const NEBIUS_MODEL = Deno.env.get("NEBIUS_MODEL") || "Qwen/Qwen3-30B-A3B";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

export default async function (req: Request): Promise<Response> {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
  if (req.method === "GET") {
    return new Response(JSON.stringify({ status: "ok", service: "phonebio-llm", model: NEBIUS_MODEL }), {
      status: 200, headers: { ...cors, "Content-Type": "application/json" },
    });
  }

  const key = Deno.env.get("NEBIUS_API_KEY");
  if (!key) {
    return new Response(JSON.stringify({ error: "NEBIUS_API_KEY secret not set" }), {
      status: 500, headers: { ...cors, "Content-Type": "application/json" },
    });
  }

  let body: any = {};
  try { body = await req.json(); } catch { /* empty */ }

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

  const upstream = await fetch(`${NEBIUS_BASE}/chat/completions`, {
    method: "POST",
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  // Stream the upstream body straight back (works for SSE stream and JSON alike).
  return new Response(upstream.body, {
    status: upstream.status,
    headers: {
      ...cors,
      "Content-Type": upstream.headers.get("content-type") || "application/json",
    },
  });
}
