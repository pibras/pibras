import { createServer, type IncomingMessage, type ServerResponse, type Server } from "node:http";
import { timingSafeEqual } from "node:crypto";
import { Buffer } from "node:buffer";
import {
  RawReceiver,
  GenericCSVMapper,
  KenloMapper,
  ZapXMLMapper,
  UnitMatcher,
  SurvivorshipArbitrator,
  ExposurePolicyEvaluator,
  TwentyCRMSync,
  PortalXMLGenerator,
  type RawIngestionPayload,
  type KenloRawPayload,
  type ArbitrationInput,
  type UnitMatchCandidate,
} from "../index.ts";
import type { Property, Unit, ExposurePolicy, MediaAsset } from "../../types/mbras.ts";

export interface ServerOptions {
  port?: number | undefined;
  host?: string | undefined;
}

export function parseJsonBody<T = unknown>(req: IncomingMessage): Promise<T> {
  return new Promise((resolve, reject) => {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk.toString();
    });
    req.on("end", () => {
      try {
        if (!body.trim()) {
          resolve({} as T);
        } else {
          resolve(JSON.parse(body) as T);
        }
      } catch (err) {
        reject(new Error(`Invalid JSON payload: ${(err as Error).message}`));
      }
    });
    req.on("error", reject);
  });
}

export function sendJson(res: ServerResponse, statusCode: number, data: unknown): void {
  res.writeHead(statusCode, { "Content-Type": "application/json; charset=utf-8" });
  res.end(JSON.stringify(data, null, 2));
}

export function sendXml(res: ServerResponse, statusCode: number, xml: string): void {
  res.writeHead(statusCode, { "Content-Type": "application/xml; charset=utf-8" });
  res.end(xml);
}

/**
 * Extrai e valida a credencial portadora exigida por `openapi.yaml`.
 *
 * O contrato declara `security: [{ bearerAuth: [] }]` globalmente, com 401 e
 * 403 em todas as operações. Servir as rotas sem credencial tornaria a
 * implementação de referência não conforme ao próprio contrato publicado.
 *
 * O token esperado vem de PIBRAS_API_TOKEN. Sem essa variável o servidor
 * recusa toda rota autenticada: falhar fechado é a única opção segura, já que
 * um default embutido viraria credencial pública.
 */
export function authorize(req: IncomingMessage): { ok: true } | { ok: false; status: 401 | 403; error: string } {
  const expected = process.env["PIBRAS_API_TOKEN"];
  const header = req.headers.authorization;

  if (!header || !header.startsWith("Bearer ")) {
    return { ok: false, status: 401, error: "Missing bearer credential" };
  }
  if (!expected) {
    return { ok: false, status: 403, error: "Server has no PIBRAS_API_TOKEN configured; authenticated routes are disabled" };
  }
  const presented = header.slice("Bearer ".length).trim();
  if (presented.length !== expected.length || !timingSafeEqual(Buffer.from(presented), Buffer.from(expected))) {
    return { ok: false, status: 403, error: "Invalid bearer credential" };
  }
  return { ok: true };
}

export function createPibrasApiServer(): Server {
  return createServer(async (req, res) => {
    const url = new URL(req.url ?? "/", `http://${req.headers.host ?? "localhost"}`);
    const method = req.method?.toUpperCase();

    // CORS headers
    // Wildcard CORS numa API autenticada permitiria que qualquer página
    // enviasse requisições; a origem permitida é explícita.
    res.setHeader("Access-Control-Allow-Origin", process.env["PIBRAS_ALLOWED_ORIGIN"] ?? "http://localhost:3000");
    res.setHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    res.setHeader("Access-Control-Allow-Headers", "Content-Type, Authorization");

    if (method === "OPTIONS") {
      res.writeHead(204);
      res.end();
      return;
    }

    try {
      // 1. Health check
      // /health permanece público para liveness probes; todo o resto exige
      // credencial portadora, conforme openapi.yaml.
      if (url.pathname !== "/health") {
        const auth = authorize(req);
        if (!auth.ok) {
          res.setHeader("WWW-Authenticate", 'Bearer realm="pibras"');
          sendJson(res, auth.status, { success: false, error: auth.error });
          return;
        }
      }

      if (url.pathname === "/health" && method === "GET") {
        sendJson(res, 200, {
          status: "ok",
          version: "0.1.0",
          timestamp: new Date().toISOString(),
        });
        return;
      }

      // 2. Ingest Raw Payload
      if (url.pathname === "/api/v1/ingest/raw" && method === "POST") {
        const body = await parseJsonBody<RawIngestionPayload>(req);
        const receipt = RawReceiver.receive(body);
        sendJson(res, 201, { success: true, data: receipt });
        return;
      }

      // 3. Ingest CSV Row
      if (url.pathname === "/api/v1/ingest/csv-row" && method === "POST") {
        const body = await parseJsonBody<{ row: Record<string, unknown>; batch_id?: string | undefined }>(req);
        const options = body.batch_id ? { batch_id: body.batch_id } : undefined;
        const mapped = GenericCSVMapper.mapRow(body.row || {}, options);
        sendJson(res, 201, { success: true, data: mapped });
        return;
      }

      // 4. Ingest Kenlo Webhook
      if (url.pathname === "/api/v1/ingest/kenlo" && method === "POST") {
        const body = await parseJsonBody<KenloRawPayload>(req);
        const mapped = KenloMapper.map(body);
        sendJson(res, 201, { success: true, data: mapped });
        return;
      }

      // 5. Ingest Zap XML Item
      if (url.pathname === "/api/v1/ingest/zap-xml" && method === "POST") {
        const body = await parseJsonBody<{ xml_item: string; batch_id?: string | undefined }>(req);
        const options = body.batch_id ? { batch_id: body.batch_id } : undefined;
        const mapped = ZapXMLMapper.mapXmlItem(body.xml_item || "", options);
        sendJson(res, 201, { success: true, data: mapped });
        return;
      }

      // 6. Dedupe Match
      if (url.pathname === "/api/v1/dedupe/match" && method === "POST") {
        const body = await parseJsonBody<{ incoming_unit: Unit; existing_inventory: UnitMatchCandidate[] }>(req);
        const matchResult = UnitMatcher.match(body.incoming_unit, body.existing_inventory || []);
        sendJson(res, 200, { success: true, data: matchResult });
        return;
      }

      // 7. Survivorship Arbitrate
      if (url.pathname === "/api/v1/survivorship/arbitrate" && method === "POST") {
        const body = await parseJsonBody<ArbitrationInput>(req);
        const result = SurvivorshipArbitrator.arbitrate(body);
        sendJson(res, 200, { success: true, data: result });
        return;
      }

      // 8. Exposure Policy Project
      if (url.pathname === "/api/v1/policy/project" && method === "POST") {
        const body = await parseJsonBody<{
          property: Property;
          unit?: Unit | undefined;
          media_assets?: MediaAsset[] | undefined;
          policy: ExposurePolicy;
          channel_type: "website" | "portal" | "crm" | "broker_network" | "paid_ad";
          caller_role: string;
        }>(req);

        const projection = ExposurePolicyEvaluator.projectForChannel({
          property: body.property,
          unit: body.unit,
          media_assets: body.media_assets,
          policy: body.policy,
          context: {
            action: "publish",
            channel_type: body.channel_type,
            caller_role: body.caller_role,
          },
        });

        sendJson(res, 200, { success: true, data: projection });
        return;
      }

      // 9. TwentyCRM Inbound
      if (url.pathname === "/api/v1/crm/twenty/from" && method === "POST") {
        const body = await parseJsonBody<{
          payload: Parameters<typeof TwentyCRMSync.fromTwentyCRM>[0]["twentyPayload"];
          currentProperty: Property | null;
          currentUnit: Unit | null;
        }>(req);

        const result = TwentyCRMSync.fromTwentyCRM({
          twentyPayload: body.payload,
          currentProperty: body.currentProperty,
          currentUnit: body.currentUnit,
        });

        sendJson(res, 200, { success: true, data: result });
        return;
      }

      // 10. Generate Portal XML Feed
      if (url.pathname === "/api/v1/feeds/portal" && method === "POST") {
        const body = await parseJsonBody<{
          items: Parameters<typeof PortalXMLGenerator.generateZapXml>[0];
          format?: "zap" | "pibras" | undefined;
        }>(req);

        const format = body.format ?? "pibras";
        const xml =
          format === "zap"
            ? PortalXMLGenerator.generateZapXml(body.items || [])
            : PortalXMLGenerator.generatePibrasXml(body.items || []);

        sendXml(res, 200, xml);
        return;
      }

      // 404 Not Found
      sendJson(res, 404, {
        success: false,
        error: "Route not found",
        path: url.pathname,
      });
    } catch (error) {
      sendJson(res, 500, {
        success: false,
        error: (error as Error).message,
      });
    }
  });
}

/**
 * Sobe o servidor de referência. `npm run serve` executa este módulo
 * diretamente; antes, nenhum listener era aberto e o processo encerrava
 * imediatamente.
 */
export function startPibrasApiServer(options: ServerOptions = {}): Server {
  const port = options.port ?? Number(process.env["PORT"] ?? 3000);
  const host = options.host ?? process.env["HOST"] ?? "127.0.0.1";
  const server = createPibrasApiServer();
  server.listen(port, host, () => {
    console.log(`PIBRAS reference API listening on http://${host}:${port}`);
    if (!process.env["PIBRAS_API_TOKEN"]) {
      console.warn("PIBRAS_API_TOKEN is not set: authenticated routes will reject every request.");
    }
  });
  return server;
}

if (import.meta.main) {
  startPibrasApiServer();
}
