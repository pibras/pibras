import { readFileSync, writeFileSync } from "node:fs";
import {
  GenericCSVMapper,
  KenloMapper,
  ZapXMLMapper,
  PortalXMLGenerator,
  type KenloRawPayload,
} from "../index.ts";

export interface CLIResult {
  command: string;
  success: boolean;
  total_processed: number;
  message: string;
  output?: unknown;
}

export class PibrasCLI {
  public static runCsvImport(filePath: string): CLIResult {
    const content = readFileSync(filePath, "utf-8");
    const lines = content.split("\n").filter((l) => l.trim().length > 0);
    if (lines.length < 2) {
      return {
        command: "import-csv",
        success: false,
        total_processed: 0,
        message: "CSV file must contain a header and at least one row.",
      };
    }

    const headers = lines[0]!.split(",").map((h) => h.trim().toLowerCase());
    const results = [];

    for (let i = 1; i < lines.length; i++) {
      const cols = lines[i]!.split(",").map((c) => c.trim());
      const row: Record<string, unknown> = {};
      headers.forEach((h, idx) => {
        row[h] = cols[idx];
      });
      const mapped = GenericCSVMapper.mapRow(row);
      results.push(mapped);
    }

    return {
      command: "import-csv",
      success: true,
      total_processed: results.length,
      message: `Successfully mapped ${results.length} CSV rows to PIBRAS canonical entities.`,
      output: results,
    };
  }

  public static runKenloImport(filePath: string): CLIResult {
    const content = readFileSync(filePath, "utf-8");
    const parsed = JSON.parse(content);
    const items: KenloRawPayload[] = Array.isArray(parsed) ? parsed : [parsed];

    const results = items.map((item) => KenloMapper.map(item));

    return {
      command: "import-kenlo",
      success: true,
      total_processed: results.length,
      message: `Successfully mapped ${results.length} Kenlo record(s) to PIBRAS canonical entities.`,
      output: results,
    };
  }

  public static runXmlImport(filePath: string): CLIResult {
    const content = readFileSync(filePath, "utf-8");
    const xmlItems = ZapXMLMapper.splitXmlItems(content);

    const results = xmlItems.map((item) => ZapXMLMapper.mapXmlItem(item));

    return {
      command: "import-xml",
      success: true,
      total_processed: results.length,
      message: `Successfully parsed and mapped ${results.length} XML item(s).`,
      output: results,
    };
  }

  public static runFeedGeneration(params: {
    items: Parameters<typeof PortalXMLGenerator.generateZapXml>[0];
    format?: "zap" | "pibras";
    outputPath?: string;
  }): CLIResult {
    const format = params.format ?? "pibras";
    const xml =
      format === "zap"
        ? PortalXMLGenerator.generateZapXml(params.items)
        : PortalXMLGenerator.generatePibrasXml(params.items);

    if (params.outputPath) {
      writeFileSync(params.outputPath, xml, "utf-8");
    }

    return {
      command: "generate-feed",
      success: true,
      total_processed: params.items.length,
      message: `Successfully generated ${format.toUpperCase()} XML feed for ${params.items.length} item(s).`,
      output: xml,
    };
  }
}

// Entrypoint quando executado via terminal
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);
  const command = args[0];
  const targetFile = args[1];

  if (!command || !targetFile) {
    console.log("Usage: pibras-cli <import-csv|import-kenlo|import-xml> <filepath>");
    process.exit(1);
  }

  let res: CLIResult;
  if (command === "import-csv") res = PibrasCLI.runCsvImport(targetFile);
  else if (command === "import-kenlo") res = PibrasCLI.runKenloImport(targetFile);
  else if (command === "import-xml") res = PibrasCLI.runXmlImport(targetFile);
  else {
    console.error(`Unknown command: ${command}`);
    process.exit(1);
  }

  console.log(JSON.stringify(res, null, 2));
}
