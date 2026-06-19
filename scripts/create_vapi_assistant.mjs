import { readFile } from "node:fs/promises";

const apiKey = process.env.VAPI_PRIVATE_KEY;
if (!apiKey) {
  console.error("Missing VAPI_PRIVATE_KEY. Refusing to call Vapi API.");
  process.exit(1);
}

const configPath = new URL("../vapi/assistant.field-biology-worker.json", import.meta.url);
const assistant = JSON.parse(await readFile(configPath, "utf8"));

const response = await fetch("https://api.vapi.ai/assistant", {
  method: "POST",
  headers: {
    authorization: `Bearer ${apiKey}`,
    "content-type": "application/json"
  },
  body: JSON.stringify(assistant)
});

const body = await response.text();
if (!response.ok) {
  console.error(`Vapi assistant creation failed: ${response.status}`);
  console.error(body);
  process.exit(1);
}

console.log(body);

