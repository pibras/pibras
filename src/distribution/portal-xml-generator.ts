import type {
  Property,
  Unit,
  MediaAsset,
  ExposurePolicy,
  ChannelType,
} from "../../types/mbras.ts";
import {
  ExposurePolicyEvaluator,
  type ApprovalRecord,
} from "../policy/evaluator.ts";

export interface FeedItemInput {
  property: Property;
  unit?: Unit | null | undefined;
  media_assets?: MediaAsset[] | undefined;
  policy: ExposurePolicy;
  approval_record?: ApprovalRecord | null | undefined;
}

export function escapeXml(str?: string | null | undefined): string {
  if (!str) return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export class PortalXMLGenerator {
  /**
   * Gera feed no padrão canônico PIBRAS XML.
   */
  public static generatePibrasXml(
    items: FeedItemInput[],
    channelType: ChannelType = "portal",
    callerRole = "portal_feed"
  ): string {
    const lines: string[] = ['<?xml version="1.0" encoding="UTF-8"?>', "<Listings>"];

    for (const item of items) {
      const projection = ExposurePolicyEvaluator.projectForChannel({
        property: item.property,
        unit: item.unit,
        media_assets: item.media_assets,
        policy: item.policy,
        context: {
          action: "publish",
          channel_type: channelType,
          caller_role: callerRole,
        },
        approval_record: item.approval_record,
      });

      // Se negado pela política/approval gate, ignora no feed
      if (!projection || projection.evaluation.decision === "deny") {
        continue;
      }

      const p = projection.property;
      const u = projection.unit;
      const code = p.code ?? p.id;
      const priceDisplay = p.asking_price ? "visible" : "on_request";
      const addressDisplay = u?.address?.street ? (u.address.number ? "full" : "approximate") : "approximate";

      lines.push("  <Listing>");
      lines.push(`    <ExternalId namespace="mbras" key="property_code">${escapeXml(code)}</ExternalId>`);
      lines.push(`    <TransactionType>${escapeXml(p.transaction_type ?? "sale")}</TransactionType>`);
      lines.push(`    <Title>${escapeXml(p.headline ?? "Imóvel")}</Title>`);
      lines.push(`    <PriceDisplay>${priceDisplay}</PriceDisplay>`);
      if (p.asking_price) {
        lines.push(`    <Price>${(p.asking_price.amount / 100).toFixed(0)}</Price>`);
      }
      lines.push(`    <AddressDisplay>${addressDisplay}</AddressDisplay>`);
      if (u?.address?.neighborhood_raw) {
        lines.push(`    <Neighborhood>${escapeXml(u.address.neighborhood_raw)}</Neighborhood>`);
      }
      if (u?.address?.city) {
        lines.push(`    <City>${escapeXml(u.address.city)}</City>`);
      }
      if (u?.usable_area_m2) {
        lines.push(`    <LivingArea>${u.usable_area_m2}</LivingArea>`);
      }
      if (u?.bedrooms) {
        lines.push(`    <Bedrooms>${u.bedrooms}</Bedrooms>`);
      }
      if (projection.media_assets.length > 0) {
        lines.push("    <Media>");
        for (const media of projection.media_assets) {
          lines.push(`      <Item role="${escapeXml(media.media_role)}">${escapeXml(media.url)}</Item>`);
        }
        lines.push("    </Media>");
      }
      lines.push("  </Listing>");
    }

    lines.push("</Listings>");
    return lines.join("\n");
  }

  /**
   * Gera feed no padrão ZAP / VivaReal XML (<Carga><Imoveis>...).
   */
  public static generateZapXml(
    items: FeedItemInput[],
    channelType: ChannelType = "portal",
    callerRole = "portal_feed"
  ): string {
    const lines: string[] = [
      '<?xml version="1.0" encoding="UTF-8"?>',
      "<Carga>",
      "  <Imoveis>",
    ];

    for (const item of items) {
      const projection = ExposurePolicyEvaluator.projectForChannel({
        property: item.property,
        unit: item.unit,
        media_assets: item.media_assets,
        policy: item.policy,
        context: {
          action: "publish",
          channel_type: channelType,
          caller_role: callerRole,
        },
        approval_record: item.approval_record,
      });

      if (!projection || projection.evaluation.decision === "deny") {
        continue;
      }

      const p = projection.property;
      const u = projection.unit;
      const code = p.code ?? p.id;

      lines.push("    <Imovel>");
      lines.push(`      <CodigoImovel>${escapeXml(code)}</CodigoImovel>`);
      lines.push(`      <TipoImovel>${escapeXml(u?.property_type ?? "Apartamento")}</TipoImovel>`);
      lines.push(`      <Finalidade>${escapeXml(p.transaction_type === "rent" ? "Locacao" : "Venda")}</Finalidade>`);
      lines.push(`      <Titulo>${escapeXml(p.headline ?? "")}</Titulo>`);
      lines.push(`      <Descricao>${escapeXml(p.summary ?? "")}</Descricao>`);
      if (p.asking_price) {
        lines.push(`      <PrecoVenda>${(p.asking_price.amount / 100).toFixed(0)}</PrecoVenda>`);
      }
      if (u?.usable_area_m2) {
        lines.push(`      <AreaUtil>${u.usable_area_m2}</AreaUtil>`);
      }
      if (u?.bedrooms) {
        lines.push(`      <QtdDormitorios>${u.bedrooms}</QtdDormitorios>`);
      }
      if (u?.suites) {
        lines.push(`      <QtdSuites>${u.suites}</QtdSuites>`);
      }
      if (u?.parking_spaces) {
        lines.push(`      <QtdVagas>${u.parking_spaces}</QtdVagas>`);
      }

      lines.push("      <Endereco>");
      if (u?.address?.street) lines.push(`        <Logradouro>${escapeXml(u.address.street)}</Logradouro>`);
      if (u?.address?.number) lines.push(`        <Numero>${escapeXml(u.address.number)}</Numero>`);
      if (u?.address?.neighborhood_raw) lines.push(`        <Bairro>${escapeXml(u.address.neighborhood_raw)}</Bairro>`);
      if (u?.address?.city) lines.push(`        <Cidade>${escapeXml(u.address.city)}</Cidade>`);
      if (u?.address?.state) lines.push(`        <Estado>${escapeXml(u.address.state)}</Estado>`);
      lines.push("      </Endereco>");

      if (projection.media_assets.length > 0) {
        lines.push("      <Fotos>");
        for (const media of projection.media_assets) {
          lines.push(`        <Foto>${escapeXml(media.url)}</Foto>`);
        }
        lines.push("      </Fotos>");
      }

      lines.push("    </Imovel>");
    }

    lines.push("  </Imoveis>");
    lines.push("</Carga>");
    return lines.join("\n");
  }
}
