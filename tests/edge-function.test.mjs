import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("InsForge Vapi webhook returns object tool results", async () => {
  const source = await readFile(new URL("../functions/vapi-webhook.ts", import.meta.url), "utf8");

  assert.match(source, /results\.push\(\{\s*toolCallId: id,\s*name,\s*result\s*\}\)/s);
  assert.doesNotMatch(source, /result:\s*JSON\.stringify\(result\)/);
});
