import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const knowledgePath = join(__dirname, "..", "data", "knowledge.json");

let cache;

export async function loadKnowledge() {
  if (!cache) {
    cache = JSON.parse(await readFile(knowledgePath, "utf8"));
  }
  return cache;
}

function normalize(value) {
  return String(value ?? "").toLowerCase();
}

function scoreRecord(record, query) {
  const haystack = [
    record.title,
    record.substance,
    record.name,
    record.guidance,
    ...(record.keywords ?? []),
    ...(record.sensors ?? [])
  ]
    .map(normalize)
    .join(" ");
  const terms = normalize(query).split(/[^a-z0-9]+/).filter(Boolean);
  return terms.reduce((score, term) => score + (haystack.includes(term) ? 1 : 0), 0);
}

function bestMatch(records, query) {
  return records
    .map((record) => ({ record, score: scoreRecord(record, query) }))
    .sort((a, b) => b.score - a.score)[0];
}

export async function getProtocol(args = {}) {
  const knowledge = await loadKnowledge();
  const query = [args.task, args.organism, args.hazard, args.description].filter(Boolean).join(" ");
  const match = bestMatch(knowledge.protocols, query);
  if (!match || match.score === 0) {
    return {
      status: "not_found",
      answer: "No local protocol matched. Stop and call the site supervisor before improvising.",
      sourceIds: []
    };
  }
  return {
    status: "ok",
    id: match.record.id,
    title: match.record.title,
    steps: match.record.steps,
    sourceIds: match.record.sourceIds
  };
}

export async function getSafetySheet(args = {}) {
  const knowledge = await loadKnowledge();
  const query = [args.substance, args.hazard, args.description].filter(Boolean).join(" ");
  const match = bestMatch(knowledge.safetySheets, query);
  if (!match || match.score === 0) {
    return {
      status: "not_found",
      answer: "No local safety summary matched. Isolate the material if safe, avoid mixing chemicals, and escalate.",
      sourceIds: []
    };
  }
  return {
    status: "ok",
    id: match.record.id,
    substance: match.record.substance,
    hazards: match.record.hazards,
    firstActions: match.record.firstActions,
    sourceIds: match.record.sourceIds
  };
}

export async function troubleshootHardware(args = {}) {
  const knowledge = await loadKnowledge();
  const query = [args.device, args.symptom, args.description].filter(Boolean).join(" ");
  const match = bestMatch(knowledge.hardware, query);
  if (!match || match.score === 0) {
    return {
      status: "not_found",
      answer: "No local hardware guide matched. Power down if unsafe and call the equipment owner.",
      sourceIds: []
    };
  }
  return {
    status: "ok",
    id: match.record.id,
    device: match.record.name,
    checks: match.record.checks,
    stopConditions: match.record.stopConditions
  };
}

export async function interpretSensorReport(args = {}) {
  const knowledge = await loadKnowledge();
  const query = [args.sensor, args.reading, args.context, args.description].filter(Boolean).join(" ");
  const match = bestMatch(knowledge.sensorGuidance, query);
  if (!match || match.score === 0) {
    return {
      status: "not_found",
      answer: "Sensor type not recognized. Ask for the sensor name, units, phone model, and whether the reading was repeated.",
      confidence: "unknown"
    };
  }
  return {
    status: "ok",
    id: match.record.id,
    sensors: match.record.sensors,
    guidance: match.record.guidance,
    confidence: match.record.confidence,
    measured: args.reading ?? null,
    inferenceBoundary: "This is guidance from caller-provided data, not a calibrated instrument result."
  };
}

export function compressObservation(args = {}) {
  const fields = {
    who: args.workerRole ?? "field worker",
    where: args.locationType ?? "field site",
    task: args.task ?? "unknown task",
    material: args.material ?? "unknown material",
    hazard: args.hazard ?? "none stated",
    sensor: args.sensor ?? "none stated",
    actionNeeded: args.actionNeeded ?? "next safe step"
  };
  return {
    status: "ok",
    compressed: Object.entries(fields)
      .map(([key, value]) => `${key}=${value}`)
      .join("; "),
    missingCriticalFields: Object.entries(fields)
      .filter(([, value]) => String(value).startsWith("unknown") || value === "none stated")
      .map(([key]) => key),
    note: "Compact observation record inspired by phonographic shorthand: preserve discriminating details and ask about missing safety-critical fields."
  };
}

