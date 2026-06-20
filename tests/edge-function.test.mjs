import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("InsForge Vapi webhook returns stringified tool results for Vapi", async () => {
  const source = await readFile(new URL("../functions/vapi-webhook.ts", import.meta.url), "utf8");

  assert.match(source, /Vapi REQUIRES the tool result to be a STRING/);
  assert.match(source, /result:\s*typeof result === "string" \? result : JSON\.stringify\(result\)/);
  assert.doesNotMatch(source, /results\.push\(\{\s*toolCallId: id,\s*name,\s*result\s*\}\)/s);
});

test("InsForge Vapi webhook accepts the same tool-call fields as local webhook", async () => {
  const source = await readFile(new URL("../functions/vapi-webhook.ts", import.meta.url), "utf8");

  assert.match(source, /call\.function\?\.name\s*\|\|\s*call\.name\s*\|\|\s*call\.toolName\s*\|\|\s*call\.type/);
  assert.match(source, /call\.function\?\.arguments\s*\?\?\s*call\.parameters\s*\?\?\s*call\.arguments\s*\?\?\s*call\.args/);
});
