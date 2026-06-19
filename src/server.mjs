import http from "node:http";
import {
  compressObservation,
  getProtocol,
  getSafetySheet,
  interpretSensorReport,
  troubleshootHardware
} from "./knowledge.mjs";

const port = Number(process.env.PORT ?? 3000);

const tools = {
  get_protocol: getProtocol,
  get_safety_sheet: getSafetySheet,
  troubleshoot_hardware: troubleshootHardware,
  interpret_sensor_report: interpretSensorReport,
  compress_observation: async (args) => compressObservation(args)
};

function jsonResponse(response, statusCode, payload) {
  response.writeHead(statusCode, { "content-type": "application/json" });
  response.end(JSON.stringify(payload));
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

export function createServer() {
  return http.createServer(async (request, response) => {
    try {
      if (request.method === "GET" && request.url === "/health") {
        jsonResponse(response, 200, { status: "ok", service: "phonebio-vapi-webhook" });
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

