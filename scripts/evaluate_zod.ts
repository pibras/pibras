// Validate the exact JSON inputs prepared by check_semantic_parity.py.
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";
import type { ZodType } from "zod";

const modulePath = process.argv[2];
if (!modulePath) throw new Error("missing target Zod module");
const schemas: Record<string, ZodType> = await import(pathToFileURL(modulePath).href);
const rows: { id: string; entity: string; input: unknown }[] =
  JSON.parse(readFileSync(0, "utf8"));

const results = rows.map(({ id, entity, input }) => {
  const schema = schemas[entity];
  if (!schema) throw new Error(`missing canonical Zod export: ${entity}`);
  const result = schema.safeParse(input);
  return { id, valid: result.success, output: result.success ? result.data : null };
});
process.stdout.write(JSON.stringify(results));
