// PhoneBio Vapi tool webhook — InsForge edge function (Deno Subhosting).
// Receives Vapi tool-calls, dispatches the 6 field-bio tools against the
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
  "personal protective equipment": "ppe", "negative control": "neg-ctrl",
  "positive control": "pos-ctrl", "no template control": "ntc",
  "polymerase chain reaction": "pcr", "stop work": "stop-work",
  "do not use": "dnu", "do not": "dnt",
};
const PHRASE_CODES = new Set(Object.values(PHRASES));
const STOP = new Set(["the","a","an","of","is","are","was","were","to","and","with","at","in","on","it","that","this","i","we","there","very","really","just","about"]);
const MEASURE = /(-?\d+(?:\.\d+)?)\s*(mbar|hpa|degrees|deg|rpm|xg|ul|um|mm|cm|km|kg|mg|ml|min|sec|ma|mv|ph|od|c|f|m|g|l|s|v|a|%|n)?/gi;
const LAB_BRIEF: Record<string, string> = {
  aliquot: "alq", dilution: "dil", buffer: "buf", reagent: "rgt", control: "ctrl",
  centrifuge: "cfg", rotor: "rtr", supernatant: "sup", pellet: "plt",
  vortex: "vtx", incubate: "inc", incubation: "inc", pipette: "pip",
  micropipette: "mpip", calibration: "cal", contamination: "contam",
  formaldehyde: "form", formalin: "form", ethanol: "etoh", bleach: "blch",
  hypochlorite: "hypo", centrifugation: "cfg", polymerase: "pol", reaction: "rxn",
  ph: "pH", rpm: "rpm",
};

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
    const code = PHRASE_CODES.has(tok) ? tok : (BRIEF[tok] ?? LAB_BRIEF[tok] ?? omitVowels(tok));
    tokens.push(code);
    if (code !== tok) map.push({ from: tok, to: code });
  }
  const measurements: { value: number; unit: string }[] = [];
  let mm;
  while ((mm = MEASURE.exec(text || "")) !== null) {
    if (mm[2]) measurements.push({ value: parseFloat(mm[1]), unit: mm[2].toLowerCase() });
  }
  const fieldLine = tokens.join(" ");
  const inverse: Record<string, string> = {};
  for (const [k, v] of Object.entries({ ...BRIEF, ...LAB_BRIEF, ...PHRASES })) inverse[String(v).toLowerCase()] = k;
  for (const item of map) inverse[item.to.toLowerCase()] = item.from.toLowerCase();
  return {
    field_line: fieldLine,
    voice_readback: fieldLine.split(/\s+/).map((tok) => inverse[tok.toLowerCase()] ?? tok).join(" "),
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

function assessEnvironmentRisk(a: Record<string, unknown>) {
  const text = join(a, ["hazard", "material", "audio", "vibration", "motion", "location", "connectivity", "phonePlacement", "sensorSummary", "description"]).toLowerCase();
  const high: Record<string, string> = {
    biohazard: "biohazard cue", blood: "potential biological exposure", needle: "sharps exposure",
    formaldehyde: "toxic chemical exposure", formalin: "toxic chemical exposure",
    chlorine: "toxic gas risk", ammonia: "toxic gas risk", fuel: "flammable material",
    fire: "fire", smoke: "smoke inhalation risk", spill: "spill", exposure: "exposure",
    rotor: "rotating equipment hazard", centrifuge: "rotating equipment hazard",
    structural: "structural hazard", flood: "flood hazard",
  };
  const med: Record<string, string> = {
    loud: "loud environment", machinery: "machinery nearby", vibration: "vibration",
    running: "rapid movement", pocket: "pocket sensor placement",
    "data down": "degraded connectivity", "voice only": "voice-only connectivity",
    multiple: "possible multiple speakers", "two voices": "possible multiple speakers",
    overlap: "possible overlapping speakers", wind: "weather/noise interference",
    heat: "temperature stress", cold: "temperature stress",
  };
  const highRiskCues = Object.entries(high).filter(([term]) => text.includes(term)).map(([, label]) => label);
  const contextCues = Object.entries(med).filter(([term]) => text.includes(term)).map(([, label]) => label);
  const peopleSignal = ["two voices", "multiple", "overlap", "several voices"].some((term) => text.includes(term))
    ? "possible_multiple_speakers_or_bystanders"
    : (text.includes("single") || text.includes("alone")) ? "reported_single_person" : "unknown";
  const riskLevel = highRiskCues.length ? "high" : contextCues.length >= 2 ? "medium" : contextCues.length ? "low_to_medium" : "unknown";
  const actions = ["Continue by voice; do not require app taps or camera input."];
  if (riskLevel === "high") actions.unshift("Stop work if safe, isolate the area, and contact the site supervisor or incident lead.");
  else if (riskLevel === "medium") actions.unshift("Slow down, repeat the critical reading, and confirm hazard, location, and people/injury status.");
  else actions.unshift("Ask one clarifying question: hazard, location, or sensor units.");
  if (["formaldehyde", "formalin", "chlorine", "ammonia", "fuel", "smoke"].some((term) => text.includes(term))) {
    actions.push("Move upwind or increase distance if safe; avoid inhalation and ignition sources.");
  }
  if (["biohazard", "blood", "needle", "sharps"].some((term) => text.includes(term))) {
    actions.push("Avoid contact, preserve PPE, and treat exposure status as safety-critical.");
  }
  const compact = compress((a.description as string) || text);
  return {
    status: "ok", riskLevel, peopleSignal, highRiskCues, contextCues, actions,
    compactFieldLine: compact.field_line, voiceReadback: compact.voice_readback,
    confidence: highRiskCues.length || contextCues.length ? "medium" : "low",
    inferenceBoundary: "Single-phone sensors can flag risk context and possible voice overlap; they do not prove exact speaker count, identity, or calibrated exposure level.",
  };
}

const TOOLS: Record<string, (a: Record<string, unknown>) => unknown | Promise<unknown>> = {
  get_protocol: getProtocol,
  get_safety_sheet: getSafetySheet,
  troubleshoot_hardware: troubleshootHardware,
  interpret_sensor_report: interpretSensorReport,
  compress_observation: compressObservation,
  assess_environment_risk: assessEnvironmentRisk,
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
    const name = call.function?.name || call.name || call.toolName || call.type || "";
    const id = call.id || call.toolCallId || name || "unknown";
    let args = call.function?.arguments ?? call.parameters ?? call.arguments ?? call.args ?? {};
    if (typeof args === "string") { try { args = JSON.parse(args); } catch { args = { description: args }; } }
    const fn = TOOLS[name];
    const result = fn ? await fn(args) : { status: "error", answer: `Unsupported tool: ${name}` };
    results.push({ toolCallId: id, name, result });
  }
  return json({ results });
}
