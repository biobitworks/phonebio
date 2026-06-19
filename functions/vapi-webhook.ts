// PhoneBio Vapi tool webhook — InsForge edge function (Deno Subhosting).
// Receives Vapi tool-calls, dispatches the 5 field-bio tools against the
// InsForge content tables (public-read RLS via anon key), returns Vapi results.
// No OpenAI, no external calls — answers come only from the project DB + local logic.
import { createClient } from "npm:@insforge/sdk";

const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization, x-vapi-secret",
};

function db() {
  return createClient({
    baseUrl: Deno.env.get("INSFORGE_BASE_URL"),
    anonKey: Deno.env.get("ANON_KEY"),
  });
}

// ---- keyword search (mirrors fieldbio/content.py best_match) ----
function terms(q: string): string[] {
  return (q || "").toLowerCase().split(/[^a-z0-9]+/).filter((t) => t.length > 1);
}
function score(rec: unknown, q: string): number {
  const hay = JSON.stringify(rec).toLowerCase();
  return terms(q).reduce((n, t) => n + (hay.includes(t) ? 1 : 0), 0);
}
function bestMatch<T>(rows: T[], q: string): { record: T | null; score: number } {
  let best: T | null = null;
  let bs = -1;
  for (const r of rows) {
    const s = score(r, q);
    if (s > bs) { bs = s; best = r; }
  }
  return { record: best, score: bs };
}
function join(args: Record<string, unknown>, keys: string[]): string {
  return keys.map((k) => args[k]).filter(Boolean).join(" ");
}

// ---- Gregg-style shorthand (compact port of fieldbio/shorthand.py) ----
const BRIEF: Record<string, string> = {
  specimen: "spc", sample: "smp", individual: "ind", observed: "obs", observation: "obs",
  temperature: "tmp", humidity: "hum", pressure: "prs", altitude: "alt", elevation: "elev",
  transect: "trn", quadrat: "qd", location: "loc", behavior: "bhv", juvenile: "juv",
  adult: "ad", male: "M", female: "F", approximately: "~", approx: "~", north: "N",
  south: "S", east: "E", west: "W", degrees: "deg", meters: "m", centimeters: "cm",
  millimeters: "mm", minutes: "min", count: "n", weight: "wt", length: "len",
  diameter: "dia", height: "ht", distance: "dist", vegetation: "veg", canopy: "cnpy",
  substrate: "sub", water: "h2o", burrow: "brw", nest: "nst", captured: "cap",
  released: "rel", recaptured: "recap", tagged: "tag", collected: "coll",
};
const PHRASES: Record<string, string> = {
  "no sign of": "no-sgn", "line of sight": "los", "safety data sheet": "sds",
  "personal protective equipment": "ppe", "do not": "dnt",
};
const STOP = new Set(["the","a","an","of","is","are","was","were","to","and","with","at","in","on","it","that","this","i","we","there","very","really","just","about"]);
const MEASURE = /(-?\d+(?:\.\d+)?)\s*(mm|cm|km|kg|mg|deg|degrees|hpa|mbar|ml|min|sec|m|g|l|s|%|n)?/gi;

function omitVowels(w: string): string {
  if (w.length <= 4) return w;
  const out = w[0] + w.slice(1).replace(/[aeiou]/g, "");
  return out.length >= 2 ? out : w;
}
function compress(text: string) {
  let work = (text || "").toLowerCase();
  for (const p of Object.keys(PHRASES).sort((a, b) => b.length - a.length)) {
    work = work.replaceAll(p, PHRASES[p]);
  }
  const tokens: string[] = [];
  const map: { from: string; to: string }[] = [];
  for (const raw of work.split(/\s+/)) {
    const m = raw.match(/[a-z][a-z'-]*/);
    const tok = m ? m[0] : raw;
    if (!tok || STOP.has(tok)) continue;
    const code = BRIEF[tok] ?? omitVowels(tok);
    tokens.push(code);
    if (code !== tok) map.push({ from: tok, to: code });
  }
  const measurements: { value: number; unit: string }[] = [];
  let mm;
  while ((mm = MEASURE.exec(text || "")) !== null) {
    if (mm[2]) measurements.push({ value: parseFloat(mm[1]), unit: mm[2].toLowerCase() });
  }
  const fieldLine = tokens.join(" ");
  return {
    field_line: fieldLine,
    measurements,
    token_map: map,
    original: text,
    compression_ratio: Math.round((fieldLine.length / Math.max((text || "").length, 1)) * 1000) / 1000,
  };
}

// ---- tools ----
async function getProtocol(a: Record<string, unknown>) {
  const { data } = await db().database.from("protocols").select("*");
  const m = bestMatch(data || [], join(a, ["task", "organism", "hazard", "description"]));
  if (!m.record || m.score <= 0) {
    return { status: "not_found", answer: "No local protocol matched. Stop and call the site supervisor before improvising.", sourceIds: [] };
  }
  const r: any = m.record;
  return { status: "ok", id: r.id, title: r.title, readAloudSummary: r.read_aloud_summary || r.title, hazards: r.hazards, body: r.body_markdown, sourceIds: [r.source_path] };
}
async function getSafetySheet(a: Record<string, unknown>) {
  const { data } = await db().database.from("safety_sheets").select("*");
  const m = bestMatch(data || [], join(a, ["substance", "hazard", "description"]));
  if (!m.record || m.score <= 0) {
    return { status: "not_found", answer: "No local safety summary matched. Isolate the material if safe, avoid mixing chemicals, and escalate.", sourceIds: [] };
  }
  const r: any = m.record;
  return { status: "ok", id: r.id, name: r.name, disclaimer: r.disclaimer, hazards: r.hazards, ppe: r.ppe, firstAid: r.first_aid, sourceIds: [r.source_path] };
}
async function troubleshootHardware(a: Record<string, unknown>) {
  const { data } = await db().database.from("hardware_guides").select("*");
  const m = bestMatch(data || [], join(a, ["device", "symptom", "description"]));
  if (!m.record || m.score <= 0) {
    return { status: "not_found", answer: "No local hardware guide matched. Power down if unsafe and call the equipment owner.", sourceIds: [] };
  }
  const r: any = m.record;
  return { status: "ok", id: r.id, device: r.device, symptom: r.symptom, steps: r.steps, escalateIf: r.escalate_if, sourceIds: [r.source_path] };
}
async function interpretSensorReport(a: Record<string, unknown>) {
  const { data } = await db().database.from("sensor_profiles").select("*");
  const m = bestMatch(data || [], join(a, ["sensor", "reading", "context", "description"]));
  if (!m.record || m.score <= 0) {
    return { status: "not_found", answer: "Sensor type not recognized. Ask for sensor name, units, phone model, and whether the reading was repeated.", confidence: "unknown" };
  }
  const r: any = m.record;
  return {
    status: "ok", id: r.id, name: r.name, measures: r.measures, accuracy: r.accuracy,
    errorSources: r.error_sources, calibration: r.calibration, voiceGuidance: r.voice_guidance,
    measured: a.reading ?? null, confidence: (r.accuracy && r.accuracy.confidence) || "unknown",
    inferenceBoundary: "Caller-provided readings are guidance, not calibrated instrument results.",
  };
}
function compressObservation(a: Record<string, unknown>) {
  const text = (a.text as string) || Object.entries(a).map(([k, v]) => `${k}: ${v}`).join("; ");
  return { status: "ok", ...compress(text) };
}

const TOOLS: Record<string, (a: Record<string, unknown>) => unknown | Promise<unknown>> = {
  get_protocol: getProtocol,
  get_safety_sheet: getSafetySheet,
  troubleshoot_hardware: troubleshootHardware,
  interpret_sensor_report: interpretSensorReport,
  compress_observation: compressObservation,
};

export default async function (req: Request): Promise<Response> {
  if (req.method === "OPTIONS") return new Response(null, { status: 204, headers: cors });
  const json = (b: unknown, s = 200) =>
    new Response(JSON.stringify(b), { status: s, headers: { ...cors, "Content-Type": "application/json" } });

  if (req.method === "GET") return json({ status: "ok", service: "phonebio-vapi-webhook" });

  // optional shared-secret check (set VAPI_WEBHOOK_SECRET as an InsForge secret)
  const secret = Deno.env.get("VAPI_WEBHOOK_SECRET");
  if (secret) {
    const got = req.headers.get("x-vapi-secret") || (req.headers.get("authorization") || "").replace("Bearer ", "");
    if (got !== secret) return json({ error: "Invalid webhook credential." }, 401);
  }

  let body: any;
  try { body = await req.json(); } catch { return json({ results: [] }); }
  const msg = body.message || body;
  const calls = msg.toolCallList || msg.toolCalls || body.toolCallList || body.toolCalls || [];

  const results = [];
  for (const call of calls) {
    const name = call.name || call.function?.name || call.type || "";
    const id = call.id || call.toolCallId || name || "unknown";
    let args = call.parameters ?? call.arguments ?? call.function?.arguments ?? {};
    if (typeof args === "string") { try { args = JSON.parse(args); } catch { args = { description: args }; } }
    const fn = TOOLS[name];
    const result = fn ? await fn(args) : { status: "error", answer: `Unsupported tool: ${name}` };
    results.push({ toolCallId: id, name, result: JSON.stringify(result) });
  }
  return json({ results });
}
