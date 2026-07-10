import { createHash } from "node:crypto"
import { mkdirSync, readFileSync, renameSync, writeFileSync } from "node:fs"
import { dirname } from "node:path"

const SOURCE_PATH = "types/mbras.ts"

class UsageError extends Error {
  readonly detail: string

  constructor(detail: string) {
    super(detail)
    this.detail = detail
    this.name = "UsageError"
  }
}

function requiredOutputPath(args: readonly string[]): string {
  const marker = args.indexOf("--out")
  const value = args[marker + 1]
  if (marker === -1 || value === undefined || value.length === 0) {
    throw new UsageError("usage: export_types_manifest.ts --out <path>")
  }
  return value
}

function sortedMatches(source: string, pattern: RegExp): readonly string[] {
  const names = new Set<string>()
  for (const match of source.matchAll(pattern)) {
    const name = match[1]
    if (name === undefined) {
      throw new UsageError("manifest export pattern did not capture a name")
    }
    names.add(name)
  }
  return [...names].sort((left, right) => left.localeCompare(right, "en"))
}

function main(): void {
  const outputPath = requiredOutputPath(process.argv.slice(2))
  const source = readFileSync(SOURCE_PATH, "utf8")
  const schemaExports = sortedMatches(source, /^export const ([A-Za-z][A-Za-z0-9_]*) =/gm)
  const typeExports = sortedMatches(source, /^export type ([A-Za-z][A-Za-z0-9_]*) =/gm)
  const manifest = {
    generated_by: "scripts/export_types_manifest.ts",
    source: SOURCE_PATH,
    source_sha256: createHash("sha256").update(source).digest("hex"),
    schema_exports: schemaExports,
    type_exports: typeExports,
  }
  const tmpPath = `${outputPath}.tmp`

  mkdirSync(dirname(outputPath), { recursive: true })
  writeFileSync(tmpPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8")
  renameSync(tmpPath, outputPath)
}

try {
  main()
} catch (error) {
  if (error instanceof UsageError) {
    console.error(error.detail)
    process.exit(64)
  }
  throw error
}
