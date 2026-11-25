#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Consumidor independente PIBRAS v0.2 (frente A10 do plano de prontidao publica).

Objetivo
    Processar imovel (Property), anuncio (Listing) e exposicao (ExposurePolicy)
    a partir da NORMA e dos EXEMPLOS PUBLICADOS, aceitando os exemplos validos e
    rejeitando os invalidos, e registrar toda interpretacao ambigua.

Independencia (regras deste arquivo)
    * Somente biblioteca padrao do Python. Nenhum pacote de terceiros.
    * Nao importa nem executa nenhum validador, mapeador ou gerador do
      repositorio (scripts/validate_*.py, scripts/check_*.py, scripts/export_*.py,
      types/, db/, src/). Nao le saidas nem relatorios desses componentes.
    * As regras abaixo foram escritas a mao a partir de docs/PIBRAS-STANDARD-v0.2.md
      (secoes 5, 6, 7), docs/exposure-policy.md, docs/rfcs/accepted-001-v0.2-reconciliation.md
      e dos exemplos publicados. As enumeracoes sao copias digitadas da norma.
    * Os exemplos (tests/golden/*.json, examples/property.sample.json) sao lidos
      apenas como DADOS. O resultado esperado e o campo publicado `expected_result`
      / `expected_decisions` / `projection_expectation` do proprio exemplo.
    * schema/mbras.schema.json e lido apenas como DADO JSON, e somente para um
      confronto de deriva (enums, campos obrigatorios, nomes de propriedades). Ele
      nao e usado como validador.

Casos executados
    published  exemplos reais do repositorio, positivos e negativos.
    derived    mutacoes em memoria dos exemplos reais (nenhum arquivo e criado ou
               alterado). Servem de negativos/positivos adicionais para anuncio e
               exposicao, que nao tem fixture negativo publicado, e para cobrir as
               regras da norma que os fixtures nao exercitam.

Uso
    python3 -I scripts/independent_consumer.py            # relatorio resumido
    python3 -I scripts/independent_consumer.py -v         # lista todos os casos
    python3 -I scripts/independent_consumer.py --json     # relatorio completo em JSON
    python3 -I scripts/independent_consumer.py --now 2026-11-25T00:00:00Z

Saida de erro: 0 = todos os casos conferem com o esperado e sem deriva;
1 = ao menos uma divergencia; 2 = erro de uso ou de leitura.
"""
from __future__ import annotations

import argparse
import copy
import json
import math
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

DEFAULT_ROOT = Path(__file__).resolve().parent.parent

# --------------------------------------------------------------------------
# Tabelas da norma (digitadas a partir da norma v0.2; nao importadas)
# --------------------------------------------------------------------------

ENUMS = {
    "SourceSystem": (
        "mbras_internal", "twenty_crm", "kenlo", "vista", "jetimob", "imobzi",
        "tecimob", "orulo", "zap_vivareal", "olx", "xml_generic", "csv_import",
        "excel_import", "manual", "other",
    ),
    "RecordState": (
        "draft", "pending_review", "active", "conflict", "duplicate", "rejected",
        "archived",
    ),
    "TransactionType": ("sale", "rent", "sale_rent", "season_rent"),
    "PropertyStatus": (
        "draft", "available", "reserved", "under_offer", "sold", "rented",
        "suspended", "off_market", "archived",
    ),
    "Availability": ("available", "unavailable", "conditioned"),
    "Currency": ("BRL", "USD", "EUR"),
    "ExposureLevel": ("public", "restricted", "confidential", "off_market"),
    "ListingStatus": ("draft", "published", "paused", "expired", "removed"),
    "PriceDisplay": ("visible", "on_request"),
    "AddressDisplay": ("full", "approximate", "hidden"),
    "OwnerRole": ("owner", "representative", "heir", "attorney"),
    "BrokerRole": ("listing", "co_listing", "capture"),
    "ComputedBy": ("human", "agent", "hermes"),
    "PolicyEffect": ("allow", "deny"),
    "PolicyAction": ("read", "write", "publish", "export", "send", "approve"),
    "PolicyDecision": ("allow", "deny", "mask", "needs_approval"),
    "PolicyResourceType": (
        "unit", "property", "listing", "media", "document", "party", "price",
        "address",
    ),
}

# Campos sensiveis (norma 7.1 + anotacoes x-pii: tax_id e min_accepted_price).
# A norma diz que a lista deve ser derivada de x-pii e "expandida"; esta e a
# leitura do consumidor (ver AMB-19).
SENSITIVE_PREFIXES = (
    "owner", "party", "min_accepted_price", "address.street", "address.number",
    "address.complement", "matricula", "unit.matricula", "document",
    "description_internal", "title_internal", "notes", "intelligence",
)
# Acoes que a norma manda negar por padrao (7.4, regra 1; exposure-policy.md, regra 2).
RESTRICTED_ACTIONS = ("write", "publish", "export", "send")

LEVEL_ORDER = {"public": 0, "restricted": 1, "confidential": 2, "off_market": 3}

ON_REQUEST_LABEL_PT = "Sob consulta"
ON_REQUEST_TOKEN = "on_request"

# Registro de interpretacoes ambiguas. `exercised` e preenchido durante a execucao.
AMBIGUITIES = [
    ("AMB-01", "Property.code x external_ids",
     "Norma 5.2 manda o codigo proprio ir para external_ids; o schema mantem `code` por compatibilidade. "
     "Aceita ambos, nao exige igualdade; registra nota quando `code` existe sem external_ids property_code."),
    ("AMB-02", "Inteiro JSON",
     "1750000000.0 e aceito como inteiro (semantica JSON Schema 2020-12). Um leitor estrito de JSON pode rejeitar. "
     "Valores integrais acima de 2^53 sao rejeitados por perda de precisao."),
    ("AMB-03", "Money.amount negativo",
     "A norma define centavos inteiros mas nao proibe valor negativo; aceito, com nota."),
    ("AMB-04", "Forma do UUID",
     "Somente a forma lexical 8-4-4-4-12 hexadecimal e verificada. Os exemplos misturam v4, v7 e valores sem "
     "variante RFC 4122; versao e variante nao sao exigidas."),
    ("AMB-05", "date-time com deslocamento",
     "O schema diz 'ISO 8601 UTC', o formato date-time (RFC 3339) aceita deslocamento numerico. "
     "Aceita Z e +hh:mm, com nota quando nao e UTC."),
    ("AMB-06", "audit.updated_at anterior a created_at",
     "Norma silenciosa; apenas nota, sem rejeitar."),
    ("AMB-07", "Soma de ownership_pct em Property.owners",
     "A regra de 100% e do DDL (trigger sobre registros ativos com papel owner). Em Property.owners, o "
     "consumidor soma os vinculos com owner_role=owner ou ausente e rejeita acima de 100."),
    ("AMB-08", "price_display x display_price",
     "Norma silenciosa sobre a coerencia: visible sem display_price, ou on_request com display_price presente. "
     "Aceita, com nota; a projecao publica suprime o valor quando on_request."),
    ("AMB-09", "Listing publicado sem exposure_level",
     "exposure_level e opcional no schema, mas property_public exige nivel publico. Ausente = nao publico (fail-closed)."),
    ("AMB-10", "Ordem de published_at e expires_at",
     "Norma silenciosa sobre expires_at <= published_at; apenas nota."),
    ("AMB-11", "Fixture 'public-masked' com exposure_level restricted",
     "O fixture se chama listing-public-masked-address mas declara exposure_level=restricted, e sua "
     "projection_expectation traz `neighborhood`, que nao e derivavel do Listing (vem de Unit/Building/Geography). "
     "Esse campo e contado como nao avaliavel, nao como acerto."),
    ("AMB-12", "Nivel do Listing x nivel da ExposurePolicy do mesmo imovel",
     "Nos exemplos publicados o Listing e restricted e a ExposurePolicy do mesmo imovel e confidential. "
     "Interpretacao: vale o mais restritivo (norma 7.4, regras 3 e 5). A ordem de off_market na escala nao e definida; "
     "usa-se a ordem do enum."),
    ("AMB-13", "'send_pdf' no exemplo da norma",
     "O exemplo de schema minimo em 7.4 usa requires_approval_for=[..., 'send_pdf'], mas o enum PolicyAction "
     "publicado so tem read/write/publish/export/send/approve. O consumidor segue o enum e rejeita 'send_pdf'."),
    ("AMB-14", "Contexto das decisoes esperadas",
     "expected_decisions nao traz contexto de avaliacao. O caso do broker espera allow numa regra com "
     "conditions.broker_is_assigned=true. Para reproduzir, o consumidor supoe um contexto que satisfaz as "
     "condicoes declaradas nas regras, e prova o inverso com contexto vazio."),
    ("AMB-15", "default_decision diferente de deny",
     "Regras 1 e 2 (campo sensivel e acao de escrita/exportacao/envio/publicacao sao default-deny) conflitam com a "
     "regra 9 (sem regra aplicavel vale default_decision) quando default_decision nao e deny. Interpretacao fail-closed: "
     "negar com reason_code sensitive_field_default_deny ou restricted_action_default_deny."),
    ("AMB-16", "reason_code ausente na regra",
     "A norma exige reason_code em toda decisao, mas a regra pode omiti-lo. Fallback do consumidor: rule_allow / rule_deny."),
    ("AMB-17", "Empate de prioridade entre regras allow",
     "A norma diz 'vence a mais restritiva' sem definir restritividade. Fallback: campo mais especifico, depois ordem declarada."),
    ("AMB-18", "Rotulo de preco sob consulta",
     "So 'Sob consulta' (pt-BR) tem evidencia publicada. Para outros locales o consumidor devolve o token on_request."),
    ("AMB-19", "Catalogo de campos sensiveis",
     "A norma lista categorias (7.1) e diz que a cobertura de x-pii deve ser expandida. O catalogo do consumidor "
     "(SENSITIVE_PREFIXES) e uma leitura propria dessas categorias, nao um contrato."),
    ("AMB-20", "Rigor do parser JSON",
     "Chaves duplicadas, NaN e Infinity sao rejeitados. JSON Schema nao define o parsing; um leitor tolerante os aceitaria."),
    ("AMB-21", "Politica em camadas",
     "A norma descreve camadas (global, tenant, recurso, canal) e que 'regra especifica do recurso vence a default'. "
     "Um unico ExposurePolicy nao permite exercitar isso; o consumidor avalia uma politica por vez."),
    ("AMB-22", "address_display=full num anuncio de nivel publico",
     "Precedencia entre address_display=full e uma politica que nega address.number ao publico nao esta definida. "
     "O consumidor aplica cada regra separadamente e nao as combina."),
    ("AMB-23", "applied_rule_ids e masked_fields",
     "applied_rule_ids e contrato de runtime fora do schema; o exemplo da norma lista varios masked_fields numa unica decisao. "
     "O consumidor devolve apenas o campo avaliado em masked_fields quando a decisao e deny ou mask."),
    ("AMB-24", "Defaults x obrigatoriedade",
     "property_status tem default draft; audit_sensitive_reads e obrigatorio e tem default true. "
     "O consumidor nunca reescreve o payload: ausente em campo obrigatorio e erro, ausente em campo opcional "
     "e lido com o default apenas na leitura (nota)."),
]


# --------------------------------------------------------------------------
# Leitura estrita de JSON
# --------------------------------------------------------------------------

def _no_dup_pairs(items):
    out = {}
    for key, value in items:
        if key in out:
            raise ValueError("chave duplicada: %r" % (key,))
        out[key] = value
    return out


def _bad_constant(name):
    raise ValueError("constante JSON nao permitida: %s" % name)


def load_json_text(text):
    return json.loads(text, object_pairs_hook=_no_dup_pairs, parse_constant=_bad_constant)


def load_json(path):
    with open(str(path), "r", encoding="utf-8") as handle:
        return load_json_text(handle.read())


# --------------------------------------------------------------------------
# Contexto de validacao
# --------------------------------------------------------------------------

class Ctx(object):
    def __init__(self):
        self.errors = []
        self.notes = []

    def err(self, path, code, message):
        self.errors.append({"path": path, "code": code, "message": message})

    def note(self, amb, path, message):
        self.notes.append({"amb": amb, "path": path, "message": message})

    def pairs(self):
        return set((e["code"], e["path"]) for e in self.errors)


# --------------------------------------------------------------------------
# Primitivas
# --------------------------------------------------------------------------

UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
DT_RE = re.compile(
    r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(\.\d+)?(Z|z|[+-]\d{2}:\d{2})$"
)
DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
URI_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:[^\s]+$")
MONEY_SCALAR_RE = re.compile(r"_(brl|usd|eur)$")


def _type_name(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, (int, float)):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    if isinstance(v, dict):
        return "object"
    return type(v).__name__


def _describe(v):
    text = repr(v)
    if len(text) > 40:
        text = text[:37] + "..."
    return "%s %s" % (_type_name(v), text)


def _is_int(v):
    if isinstance(v, bool):
        return False
    if isinstance(v, int):
        return True
    return isinstance(v, float) and v.is_integer() and abs(v) < 2 ** 53


def _is_number(v):
    if isinstance(v, bool):
        return False
    if isinstance(v, int):
        return True
    return isinstance(v, float) and math.isfinite(v)


def _parse_dt(text):
    if not isinstance(text, str):
        return None
    m = DT_RE.match(text)
    if not m:
        return None
    try:
        base = datetime(*[int(g) for g in m.groups()[:6]])
    except ValueError:
        return None
    tz = m.group(8)
    if tz in ("Z", "z"):
        offset = timezone.utc
    else:
        sign = 1 if tz[0] == "+" else -1
        hours, minutes = int(tz[1:3]), int(tz[4:6])
        if hours > 23 or minutes > 59:
            return None
        offset = timezone(sign * timedelta(hours=hours, minutes=minutes))
    return base.replace(tzinfo=offset)


def _iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def t_string(nullable=False):
    def check(v, p, ctx):
        if v is None and nullable:
            return
        if not isinstance(v, str):
            ctx.err(p, "type", "esperado string%s, recebido %s" % (" ou null" if nullable else "", _describe(v)))
    return check


def t_boolean():
    def check(v, p, ctx):
        if not isinstance(v, bool):
            ctx.err(p, "type", "esperado boolean, recebido %s" % _describe(v))
    return check


def t_integer(minimum=None, maximum=None, nullable=False):
    def check(v, p, ctx):
        if v is None and nullable:
            return
        if not _is_int(v):
            ctx.err(p, "type", "esperado inteiro%s, recebido %s" % (" ou null" if nullable else "", _describe(v)))
            return
        if isinstance(v, float):
            ctx.note("AMB-02", p, "%r aceito como inteiro" % (v,))
        n = int(v)
        if minimum is not None and n < minimum:
            ctx.err(p, "range", "%d abaixo do minimo %d" % (n, minimum))
        if maximum is not None and n > maximum:
            ctx.err(p, "range", "%d acima do maximo %d" % (n, maximum))
    return check


def t_number(minimum=None, maximum=None, nullable=False):
    def check(v, p, ctx):
        if v is None and nullable:
            return
        if not _is_number(v):
            ctx.err(p, "type", "esperado numero%s, recebido %s" % (" ou null" if nullable else "", _describe(v)))
            return
        if minimum is not None and v < minimum:
            ctx.err(p, "range", "%r abaixo do minimo %r" % (v, minimum))
        if maximum is not None and v > maximum:
            ctx.err(p, "range", "%r acima do maximo %r" % (v, maximum))
    return check


def t_uuid(nullable=False):
    def check(v, p, ctx):
        if v is None and nullable:
            return
        if not isinstance(v, str):
            ctx.err(p, "type", "esperado UUID em string, recebido %s" % _describe(v))
            return
        if not UUID_RE.match(v):
            ctx.err(p, "format", "UUID invalido: %r" % (v,))
            return
        if v[19] not in "89abAB":
            ctx.note("AMB-04", p, "UUID %s sem variante RFC 4122; aceito pela forma lexical" % v)
    return check


def t_datetime(nullable=False):
    def check(v, p, ctx):
        if v is None and nullable:
            return
        if not isinstance(v, str):
            ctx.err(p, "type", "esperado date-time em string, recebido %s" % _describe(v))
            return
        parsed = _parse_dt(v)
        if parsed is None:
            ctx.err(p, "format", "date-time invalido (RFC 3339): %r" % (v,))
            return
        if parsed.utcoffset() != timedelta(0):
            ctx.note("AMB-05", p, "date-time com deslocamento nao UTC: %s" % v)
    return check


def t_date(nullable=False):
    def check(v, p, ctx):
        if v is None and nullable:
            return
        if not isinstance(v, str):
            ctx.err(p, "type", "esperado date em string, recebido %s" % _describe(v))
            return
        m = DATE_RE.match(v)
        ok = False
        if m:
            try:
                date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                ok = True
            except ValueError:
                ok = False
        if not ok:
            ctx.err(p, "format", "date invalida (AAAA-MM-DD): %r" % (v,))
    return check


def t_uri(nullable=False):
    def check(v, p, ctx):
        if v is None and nullable:
            return
        if not isinstance(v, str):
            ctx.err(p, "type", "esperado URI em string, recebido %s" % _describe(v))
            return
        if not URI_RE.match(v):
            ctx.err(p, "format", "URI invalida: %r" % (v,))
    return check


def t_enum(name, nullable=False):
    allowed = ENUMS[name]

    def check(v, p, ctx):
        if v is None and nullable:
            return
        if not isinstance(v, str) or v not in allowed:
            ctx.err(p, "enum", "valor %s fora de %s %s" % (_describe(v), name, list(allowed)))
            if name == "PolicyAction" and v == "send_pdf":
                ctx.note("AMB-13", p, "'send_pdf' aparece no exemplo da norma, mas nao no enum PolicyAction")
    check.enum_name = name
    return check


def t_array(item, nullable=False):
    def check(v, p, ctx):
        if v is None and nullable:
            return
        if not isinstance(v, list):
            ctx.err(p, "type", "esperado array, recebido %s" % _describe(v))
            return
        for index, element in enumerate(v):
            item(element, "%s[%d]" % (p, index), ctx)
    return check


def t_free_object():
    def check(v, p, ctx):
        if not isinstance(v, dict):
            ctx.err(p, "type", "esperado objeto, recebido %s" % _describe(v))
    return check


def t_object(def_name, required, props):
    def check(v, p, ctx):
        if not isinstance(v, dict):
            ctx.err(p, "type", "esperado objeto, recebido %s" % _describe(v))
            return
        for key in required:
            if key not in v:
                ctx.err("%s.%s" % (p, key), "required", "campo obrigatorio ausente: %s" % key)
        for key, value in v.items():
            path = "%s.%s" % (p, key)
            if key in props:
                props[key](value, path, ctx)
            elif MONEY_SCALAR_RE.search(key):
                ctx.err(path, "money_scalar_field",
                        "%s: dinheiro e {amount, currency} em centavos (norma 5.1), nao escalar com moeda no nome" % key)
            else:
                ctx.err(path, "unknown_property", "propriedade nao prevista: %s" % key)
    check.def_name = def_name
    check.required = tuple(required)
    check.props = props
    return check


def check_money(v, p, ctx):
    if not isinstance(v, dict):
        ctx.err(p, "type", "Money deve ser objeto {amount, currency}, recebido %s" % _describe(v))
        return
    for key in ("amount", "currency"):
        if key not in v:
            ctx.err("%s.%s" % (p, key), "required", "campo obrigatorio ausente: %s" % key)
    for key in v:
        if key not in ("amount", "currency"):
            ctx.err("%s.%s" % (p, key), "unknown_property", "propriedade nao prevista em Money: %s" % key)
    if "amount" in v:
        amount = v["amount"]
        if not _is_int(amount):
            ctx.err("%s.amount" % p, "type", "amount deve ser inteiro em centavos, recebido %s" % _describe(amount))
        else:
            if isinstance(amount, float):
                ctx.note("AMB-02", "%s.amount" % p, "%r aceito como inteiro" % (amount,))
            if amount < 0:
                ctx.note("AMB-03", "%s.amount" % p, "valor negativo aceito: %r" % (amount,))
    if "currency" in v:
        t_enum("Currency")(v["currency"], "%s.currency" % p, ctx)


check_money.def_name = "Money"
check_money.required = ("amount", "currency")
check_money.props = {"amount": None, "currency": None}
MONEY = check_money


# --------------------------------------------------------------------------
# Entidades (Property, Listing, ExposurePolicy e dependencias)
# --------------------------------------------------------------------------

S = t_string()
SN = t_string(True)

EXTERNAL_ID = t_object("ExternalId", ["namespace", "key", "value"], {
    "namespace": S, "key": S, "value": S,
})

PROVENANCE = t_object("Provenance", ["source_system", "trust_tier", "ingested_at"], {
    "source_system": t_enum("SourceSystem"),
    "source_record_id": SN,
    "source_url": t_uri(True),
    "trust_tier": t_integer(1, 6),
    "ingested_at": t_datetime(),
    "ingested_by": SN,
    "sync_batch_id": t_uuid(True),
    "raw_payload_ref": SN,
})

DATA_QUALITY = t_object("DataQuality", [], {
    "missing_fields": t_array(S),
    "warnings": t_array(S),
})

AUDIT = t_object("AuditStamp", ["created_at", "updated_at", "version", "record_state"], {
    "created_at": t_datetime(),
    "updated_at": t_datetime(),
    "created_by": SN,
    "updated_by": SN,
    "version": t_integer(1),
    "record_state": t_enum("RecordState"),
    "completeness_score": t_integer(0, 100, True),
    "data_quality": DATA_QUALITY,
})

OWNER_LINK = t_object("PropertyOwnerLink", ["owner_id"], {
    "owner_id": t_uuid(),
    "ownership_pct": t_number(0, 100, True),
    "owner_role": t_enum("OwnerRole"),
    "is_primary": t_boolean(),
})

BROKER_LINK = t_object("PropertyBrokerLink", ["broker_id"], {
    "broker_id": t_uuid(),
    "broker_role": t_enum("BrokerRole"),
    "is_primary": t_boolean(),
    "assigned_at": t_datetime(True),
})

_score = t_integer(0, 100, True)
INTELLIGENCE = t_object("PropertyIntelligence", [], {
    "property_id": t_uuid(True),
    "ideal_buyer_profile": SN,
    "likely_objections": t_array(S),
    "selling_arguments": t_array(S),
    "privacy_level": SN,
    "rarity_score": _score,
    "architecture_notes": SN,
    "view_quality": _score,
    "natural_light": _score,
    "noise_level": _score,
    "liquidity_score": _score,
    "match_score": _score,
    "defensible_price": MONEY,
    "off_market_potential": _score,
    "demand_notes": SN,
    "last_computed_at": t_datetime(True),
    "computed_by": t_enum("ComputedBy"),
    "confidence": _score,
})

PROPERTY = t_object("Property", ["id", "unit_id", "transaction_type", "provenance", "audit"], {
    "id": t_uuid(),
    "code": SN,
    "external_ids": t_array(EXTERNAL_ID),
    "unit_id": t_uuid(),
    "building_id": t_uuid(True),
    "transaction_type": t_enum("TransactionType"),
    "property_status": t_enum("PropertyStatus"),
    "availability": t_enum("Availability"),
    "asking_price": MONEY,
    "min_accepted_price": MONEY,
    "rent_price": MONEY,
    "exclusive": t_boolean(),
    "exclusivity_until": t_date(True),
    "headline": SN,
    "summary": SN,
    "primary_broker_id": t_uuid(True),
    "published": t_boolean(),
    "last_price_change_at": t_datetime(True),
    "owners": t_array(OWNER_LINK),
    "brokers": t_array(BROKER_LINK),
    "intelligence": INTELLIGENCE,
    "provenance": PROVENANCE,
    "audit": AUDIT,
})

LISTING = t_object("Listing", [
    "id", "property_id", "channel_id", "locale", "transaction_type", "price_display",
    "address_display", "listing_status", "provenance", "audit",
], {
    "id": t_uuid(),
    "property_id": t_uuid(),
    "channel_id": t_uuid(),
    "locale": S,
    "transaction_type": t_enum("TransactionType"),
    "title_public": SN,
    "title_internal": SN,
    "description_public": SN,
    "description_internal": SN,
    "price_display": t_enum("PriceDisplay"),
    "display_price": MONEY,
    "address_display": t_enum("AddressDisplay"),
    "media_selection": t_array(t_uuid()),
    "listing_status": t_enum("ListingStatus"),
    "exposure_level": t_enum("ExposureLevel"),
    "published_at": t_datetime(True),
    "expires_at": t_datetime(True),
    "external_listing_id": SN,
    "external_url": t_uri(True),
    "provenance": PROVENANCE,
    "audit": AUDIT,
})

RULE = t_object("ExposurePolicyRule", ["effect", "actions"], {
    "id": t_uuid(),
    "priority": t_integer(),
    "effect": t_enum("PolicyEffect"),
    "actions": t_array(t_enum("PolicyAction")),
    "fields": t_array(S),
    "roles": t_array(S),
    "conditions": t_free_object(),
    "reason_code": SN,
})

POLICY = t_object("ExposurePolicy", [
    "id", "resource_type", "exposure_level", "default_decision", "audit_sensitive_reads",
    "created_at", "updated_at",
], {
    "id": t_uuid(),
    "tenant_id": t_uuid(True),
    "resource_type": t_enum("PolicyResourceType"),
    "resource_id": t_uuid(True),
    "exposure_level": t_enum("ExposureLevel"),
    "rules": t_array(RULE),
    "requires_approval_for": t_array(t_enum("PolicyAction")),
    "allowed_channels": t_array(S),
    "default_decision": t_enum("PolicyDecision"),
    "audit_sensitive_reads": t_boolean(),
    "created_at": t_datetime(),
    "updated_at": t_datetime(),
})

SPEC_BY_DEF = {
    "Property": PROPERTY, "Listing": LISTING, "ExposurePolicy": POLICY,
    "ExposurePolicyRule": RULE, "Money": MONEY, "Provenance": PROVENANCE,
    "AuditStamp": AUDIT, "ExternalId": EXTERNAL_ID, "PropertyOwnerLink": OWNER_LINK,
    "PropertyBrokerLink": BROKER_LINK,
}


# --------------------------------------------------------------------------
# Regras semanticas da norma (alem da forma)
# --------------------------------------------------------------------------

def _audit_semantics(doc, ctx):
    audit = doc.get("audit")
    if not isinstance(audit, dict):
        return
    created = _parse_dt(audit.get("created_at"))
    updated = _parse_dt(audit.get("updated_at"))
    if created is not None and updated is not None and updated < created:
        ctx.note("AMB-06", "$.audit.updated_at", "updated_at anterior a created_at")


def validate_property(doc, ctx):
    PROPERTY(doc, "$", ctx)
    if not isinstance(doc, dict):
        return
    _audit_semantics(doc, ctx)
    code = doc.get("code")
    if isinstance(code, str):
        external = doc.get("external_ids")
        values = []
        if isinstance(external, list):
            for entry in external:
                if isinstance(entry, dict) and entry.get("key") == "property_code":
                    values.append(entry.get("value"))
        if not values:
            ctx.note("AMB-01", "$.code", "codigo legado sem external_ids property_code")
        elif code not in values:
            ctx.note("AMB-01", "$.code", "code diverge de external_ids property_code")
    if "property_status" not in doc:
        ctx.note("AMB-24", "$.property_status", "ausente; lido como draft (default do schema), payload nao e reescrito")
    owners = doc.get("owners")
    if isinstance(owners, list):
        total = 0.0
        for index, link in enumerate(owners):
            if not isinstance(link, dict):
                continue
            role = link.get("owner_role")
            if role not in (None, "owner"):
                continue
            if role is None:
                ctx.note("AMB-07", "$.owners[%d]" % index, "owner_role ausente contado como owner")
            pct = link.get("ownership_pct")
            if _is_number(pct):
                total += pct
        if total > 100 + 1e-9:
            ctx.err("$.owners", "ownership_over_100", "soma de ownership_pct (%s) acima de 100" % total)


def validate_listing(doc, ctx):
    LISTING(doc, "$", ctx)
    if not isinstance(doc, dict):
        return
    _audit_semantics(doc, ctx)
    display = doc.get("price_display")
    if display == "visible" and "display_price" not in doc:
        ctx.note("AMB-08", "$.display_price", "price_display=visible sem display_price")
    if display == "on_request" and doc.get("display_price") is not None:
        ctx.note("AMB-08", "$.display_price", "display_price presente com on_request; a projecao deve suprimir")
    if doc.get("listing_status") == "published" and "exposure_level" not in doc:
        ctx.note("AMB-09", "$.exposure_level", "publicado sem exposure_level; tratado como nao publico")
    published = _parse_dt(doc.get("published_at"))
    expires = _parse_dt(doc.get("expires_at"))
    if published is not None and expires is not None and expires <= published:
        ctx.note("AMB-10", "$.expires_at", "expires_at nao posterior a published_at")


def validate_policy(doc, ctx):
    POLICY(doc, "$", ctx)
    if not isinstance(doc, dict):
        return
    if doc.get("default_decision") not in (None, "deny"):
        ctx.note("AMB-15", "$.default_decision",
                 "default_decision=%s; campos sensiveis e acoes restritas continuam negados" % doc.get("default_decision"))


def validate_money(doc, ctx):
    check_money(doc, "$", ctx)


VALIDATORS = {
    "property": validate_property,
    "listing": validate_listing,
    "exposure_policy": validate_policy,
    "money": validate_money,
}

ENTITY_BY_REF = {
    "#/$defs/Property": "property",
    "#/$defs/Listing": "listing",
    "#/$defs/ExposurePolicy": "exposure_policy",
    "#/$defs/Money": "money",
}


# --------------------------------------------------------------------------
# Processamento: dinheiro, projecao do anuncio, elegibilidade, decisao de politica
# --------------------------------------------------------------------------

def format_money(money):
    amount = int(money["amount"])
    currency = money["currency"]
    sign = "-" if amount < 0 else ""
    major, minor = divmod(abs(amount), 100)
    if currency == "BRL":
        return "%sR$ %s,%02d" % (sign, ("{:,}".format(major)).replace(",", "."), minor)
    return "%s%s %s.%02d" % (sign, currency, "{:,}".format(major), minor)


def is_sensitive(field):
    if field == "tax_id" or field.endswith(".tax_id"):
        return True
    for prefix in SENSITIVE_PREFIXES:
        if field == prefix or field.startswith(prefix + "."):
            return True
    return False


def project_listing(listing, address=None, neighborhood=None):
    """Projecao mascarada do anuncio. Devolve (view, unresolved, notes)."""
    view = {}
    unresolved = []
    notes = []
    locale = str(listing.get("locale") or "")
    if listing.get("price_display") == "visible":
        display_price = listing.get("display_price")
        view["price"] = format_money(display_price) if isinstance(display_price, dict) else None
    elif locale.lower().startswith("pt"):
        view["price"] = ON_REQUEST_LABEL_PT
    else:
        view["price"] = ON_REQUEST_TOKEN
        notes.append("AMB-18")
    mode = listing.get("address_display")
    if mode == "full":
        if isinstance(address, dict) and "street" in address and "number" in address:
            view["address.street"] = address["street"]
            view["address.number"] = address["number"]
        else:
            unresolved.extend(["address.street", "address.number"])
    else:
        view["address.street"] = None
        view["address.number"] = None
    if mode == "hidden":
        view["neighborhood"] = None
    elif neighborhood is not None:
        view["neighborhood"] = neighborhood
    else:
        unresolved.append("neighborhood")
    return view, unresolved, notes


def check_leaks(listing, view):
    codes = []
    if listing.get("price_display") != "visible":
        if view.get("price") not in (None, ON_REQUEST_LABEL_PT, ON_REQUEST_TOKEN):
            codes.append("price_leak")
    for key in ("display_price", "asking_price", "min_accepted_price"):
        if view.get(key) is not None and listing.get("price_display") != "visible":
            codes.append("price_leak")
    mode = listing.get("address_display")
    if mode != "full":
        for key in ("address.street", "address.number", "address.complement", "address.postal_code"):
            if view.get(key) is not None:
                codes.append("address_leak")
    if mode == "hidden":
        for key in ("neighborhood", "address.neighborhood", "address.city", "address.state",
                    "address.latitude", "address.longitude", "building_name"):
            if view.get(key) is not None:
                codes.append("address_leak")
    for key, value in view.items():
        if value is not None and is_sensitive(key) and not key.startswith("address."):
            codes.append("pii_leak")
    unique = []
    for code in codes:
        if code not in unique:
            unique.append(code)
    return unique


def public_eligibility(listing, now, channel_active=None, policy=None):
    """Condicoes fail-closed da superficie publica (RFC-001, secao Seguranca). Lista vazia = elegivel."""
    reasons = []
    if listing.get("exposure_level") != "public":
        reasons.append("exposure_level_not_public")
    if policy is not None and policy.get("exposure_level") != "public":
        reasons.append("policy_exposure_level_not_public")
    if listing.get("listing_status") != "published":
        reasons.append("listing_not_published")
    audit = listing.get("audit")
    state = audit.get("record_state") if isinstance(audit, dict) else None
    if state != "active":
        reasons.append("record_not_active")
    expires = listing.get("expires_at")
    if isinstance(expires, str):
        parsed = _parse_dt(expires)
        if parsed is None or parsed <= now:
            reasons.append("listing_expired")
    if channel_active is not True:
        reasons.append("channel_inactive_or_unknown")
    return reasons


def _field_specificity(rule_fields, field):
    """None = regra nao cobre o campo; inteiro = especificidade (0 para `fields` vazio)."""
    if not rule_fields:
        return 0
    best = None
    for candidate in rule_fields:
        if field == candidate or field.startswith(candidate + "."):
            if best is None or len(candidate) > best:
                best = len(candidate)
    return best


def _conditions_met(conditions, context):
    for key, expected in (conditions or {}).items():
        if key not in context or context[key] != expected:
            return False
    return True


def _decision(decision, reason, rule_ids, field, notes=None):
    return {
        "decision": decision,
        "reason_code": reason,
        "applied_rule_ids": list(rule_ids),
        "masked_fields": [field] if decision in ("deny", "mask") else [],
        "notes": list(notes or []),
    }


def decide(policy, subject_role, action, field, context=None, channel=None):
    """Avalia uma ExposurePolicy segundo docs/exposure-policy.md (regras 1 a 12)."""
    context = context or {}
    requires_approval = policy.get("requires_approval_for") or []
    allowed_channels = policy.get("allowed_channels") or []
    if channel is not None and allowed_channels and channel not in allowed_channels:
        return _decision("deny", "channel_not_allowed", [], field)
    applicable = []
    for index, rule in enumerate(policy.get("rules") or []):
        if action not in (rule.get("actions") or []):
            continue
        specificity = _field_specificity(rule.get("fields") or [], field)
        if specificity is None:
            continue
        roles = rule.get("roles") or []
        if roles and subject_role not in roles:
            continue
        if not _conditions_met(rule.get("conditions") or {}, context):
            continue
        applicable.append((rule.get("priority", 0), specificity, index, rule))
    if applicable:
        top = max(item[0] for item in applicable)
        tops = [item for item in applicable if item[0] == top]
        denies = [item for item in tops if item[3].get("effect") == "deny"]
        pool = denies or tops
        notes = []
        if not denies and len(tops) > 1:
            notes.append("AMB-17")
        chosen = sorted(pool, key=lambda item: (-item[1], item[2]))[0]
        rule = chosen[3]
        effect = rule.get("effect")
        reason = rule.get("reason_code")
        if not reason:
            reason = "rule_%s" % effect
            notes.append("AMB-16")
        decision = effect
        if effect == "allow" and action in requires_approval:
            decision = "needs_approval"
        rule_id = rule.get("id") or "rules[%d]" % chosen[2]
        return _decision(decision, reason, [rule_id], field, notes)
    default = policy.get("default_decision")
    if default == "deny":
        return _decision("deny", "default_decision", [], field)
    if is_sensitive(field):
        return _decision("deny", "sensitive_field_default_deny", [], field, ["AMB-15"])
    if action in RESTRICTED_ACTIONS:
        return _decision("deny", "restricted_action_default_deny", [], field, ["AMB-15"])
    decision = default
    if decision == "allow" and action in requires_approval:
        decision = "needs_approval"
    return _decision(decision, "default_decision", [], field)


def assumed_context(policy):
    """AMB-14: contexto que satisfaz todas as condicoes declaradas nas regras."""
    context = {}
    for rule in policy.get("rules") or []:
        for key, value in (rule.get("conditions") or {}).items():
            context[key] = value
    return context


def summarize_property(doc):
    summary = {
        "id": doc.get("id"),
        "transaction_type": doc.get("transaction_type"),
        "status": doc.get("property_status", "draft"),
        "trust_tier": (doc.get("provenance") or {}).get("trust_tier"),
    }
    price = doc.get("asking_price")
    summary["asking_price"] = format_money(price) if isinstance(price, dict) else None
    summary["restricted_fields_present"] = sorted(k for k in doc if is_sensitive(k))
    return summary


# --------------------------------------------------------------------------
# Mutacoes em memoria (casos derivados)
# --------------------------------------------------------------------------

def _set(path, value):
    def mutate(doc):
        cur = doc
        for key in path[:-1]:
            cur = cur[key]
        cur[path[-1]] = value
    return mutate


def _del(path):
    def mutate(doc):
        cur = doc
        for key in path[:-1]:
            cur = cur[key]
        del cur[path[-1]]
    return mutate


def _all(*mutations):
    def mutate(doc):
        for mutation in mutations:
            mutation(doc)
    return mutate


OWNER_A = "d5e6f7a8-9b0c-4d1e-8f2a-3b4c5d6e7f80"
OWNER_B = "e6f7a8b9-0c1d-4e2f-9a3b-4c5d6e7f8091"


def _owners(first, second):
    return [
        {"owner_id": OWNER_A, "ownership_pct": first, "owner_role": "owner", "is_primary": True},
        {"owner_id": OWNER_B, "ownership_pct": second, "owner_role": "owner"},
    ]


PROPERTY_NEGATIVES = [
    ("missing-unit-id", _del(("unit_id",)), [("required", "$.unit_id")]),
    ("missing-provenance", _del(("provenance",)), [("required", "$.provenance")]),
    ("id-not-uuid", _set(("id",), "MB18495"), [("format", "$.id")]),
    ("amount-as-string", _set(("asking_price", "amount"), "1750000000"), [("type", "$.asking_price.amount")]),
    ("amount-fractional", _set(("asking_price", "amount"), 17500000.5), [("type", "$.asking_price.amount")]),
    ("amount-boolean", _set(("asking_price", "amount"), True), [("type", "$.asking_price.amount")]),
    ("currency-unknown", _set(("asking_price", "currency"), "BRLX"), [("enum", "$.asking_price.currency")]),
    ("currency-missing", _del(("asking_price", "currency")), [("required", "$.asking_price.currency")]),
    ("asking-price-null", _set(("asking_price",), None), [("type", "$.asking_price")]),
    ("money-scalar-usd", _set(("asking_price_usd",), 100000), [("money_scalar_field", "$.asking_price_usd")]),
    ("money-extra-field", _set(("asking_price", "formatted"), "R$ 1"), [("unknown_property", "$.asking_price.formatted")]),
    ("unknown-property", _set(("owner_name",), "Fulano"), [("unknown_property", "$.owner_name")]),
    ("trust-tier-7", _set(("provenance", "trust_tier"), 7), [("range", "$.provenance.trust_tier")]),
    ("trust-tier-0", _set(("provenance", "trust_tier"), 0), [("range", "$.provenance.trust_tier")]),
    ("record-state-unknown", _set(("audit", "record_state"), "deleted"), [("enum", "$.audit.record_state")]),
    ("status-unknown", _set(("property_status",), "for_sale"), [("enum", "$.property_status")]),
    ("transaction-unknown", _set(("transaction_type",), "lease"), [("enum", "$.transaction_type")]),
    ("ingested-at-date-only", _set(("provenance", "ingested_at"), "2026-06-19"), [("format", "$.provenance.ingested_at")]),
    ("audit-version-zero", _set(("audit", "version"), 0), [("range", "$.audit.version")]),
    ("exclusivity-bad-date", _set(("exclusivity_until",), "31/12/2026"), [("format", "$.exclusivity_until")]),
    ("owners-over-100", _set(("owners",), _owners(60, 60)), [("ownership_over_100", "$.owners")]),
    ("owner-pct-out-of-range", _set(("owners",), _owners(120, 0)), [("range", "$.owners[0].ownership_pct")]),
    ("external-id-missing-value", _set(("external_ids",), [{"namespace": "mbras", "key": "property_code"}]),
     [("required", "$.external_ids[0].value")]),
]

PROPERTY_POSITIVES = [
    ("amount-integral-float", _set(("asking_price", "amount"), 1750000000.0)),
    ("currency-usd", _set(("asking_price", "currency"), "USD")),
    ("explicit-null-optionals", _all(_set(("code",), None), _set(("headline",), None))),
    ("status-omitted", _del(("property_status",))),
    ("owners-split-100", _set(("owners",), _owners(60, 40))),
    ("rent-with-rent-price", _all(_set(("transaction_type",), "rent"),
                                  _set(("rent_price",), {"amount": 1200000, "currency": "BRL"}))),
    ("offset-timestamp", _set(("provenance", "ingested_at"), "2026-06-19T09:00:00-03:00")),
]

LISTING_NEGATIVES = [
    ("missing-channel-id", _del(("channel_id",)), [("required", "$.channel_id")]),
    ("missing-locale", _del(("locale",)), [("required", "$.locale")]),
    ("status-unknown", _set(("listing_status",), "live"), [("enum", "$.listing_status")]),
    ("price-display-unknown", _set(("price_display",), "hidden"), [("enum", "$.price_display")]),
    ("address-display-unknown", _set(("address_display",), "partial"), [("enum", "$.address_display")]),
    ("exposure-level-unknown", _set(("exposure_level",), "internal"), [("enum", "$.exposure_level")]),
    ("unknown-property", _set(("owner_name",), "Fulano"), [("unknown_property", "$.owner_name")]),
    ("media-selection-not-uuid", _set(("media_selection",), ["not-a-uuid"]), [("format", "$.media_selection[0]")]),
    ("published-at-bad", _set(("published_at",), "yesterday"), [("format", "$.published_at")]),
    ("external-url-bad", _set(("external_url",), "not a url"), [("format", "$.external_url")]),
    ("display-price-fractional", _set(("display_price",), {"amount": 100.5, "currency": "BRL"}),
     [("type", "$.display_price.amount")]),
    ("display-price-scalar", _set(("display_price_brl",), 100), [("money_scalar_field", "$.display_price_brl")]),
]

LISTING_POSITIVES = [
    ("visible-with-display-price", _all(_set(("price_display",), "visible"),
                                        _set(("display_price",), {"amount": 1750000000, "currency": "BRL"}))),
    ("full-address-public", _all(_set(("address_display",), "full"), _set(("exposure_level",), "public"))),
    ("locale-en-US", _set(("locale",), "en-US")),
    ("exposure-level-omitted", _del(("exposure_level",))),
]

POLICY_NEGATIVES = [
    ("missing-default-decision", _del(("default_decision",)), [("required", "$.default_decision")]),
    ("missing-audit-flag", _del(("audit_sensitive_reads",)), [("required", "$.audit_sensitive_reads")]),
    ("default-decision-unknown", _set(("default_decision",), "maybe"), [("enum", "$.default_decision")]),
    ("rule-effect-unknown", _set(("rules", 0, "effect"), "permit"), [("enum", "$.rules[0].effect")]),
    ("action-send-pdf", _set(("requires_approval_for",), ["export", "send_pdf"]),
     [("enum", "$.requires_approval_for[1]")]),
    ("rule-unknown-property", _set(("rules", 0, "role"), "broker"), [("unknown_property", "$.rules[0].role")]),
    ("rule-missing-actions", _del(("rules", 1, "actions")), [("required", "$.rules[1].actions")]),
    ("audit-flag-string", _set(("audit_sensitive_reads",), "yes"), [("type", "$.audit_sensitive_reads")]),
    ("resource-type-unknown", _set(("resource_type",), "tenant"), [("enum", "$.resource_type")]),
    ("priority-fractional", _set(("rules", 2, "priority"), 1.5), [("type", "$.rules[2].priority")]),
    ("created-at-date-only", _set(("created_at",), "2026-06-19"), [("format", "$.created_at")]),
    ("rules-not-array", _set(("rules",), {}), [("type", "$.rules")]),
]

POLICY_POSITIVES = [
    ("default-allow-public-level", _all(_set(("exposure_level",), "public"), _set(("default_decision",), "allow"))),
    ("no-rules", _del(("rules",))),
    ("negative-priority", _set(("rules", 0, "priority"), -1)),
]


def _rule(effect, actions, fields, roles=None, priority=None, reason=None, conditions=None):
    rule = {"effect": effect, "actions": list(actions), "fields": list(fields),
            "roles": list(roles or []), "conditions": dict(conditions or {})}
    if priority is not None:
        rule["priority"] = priority
    if reason is not None:
        rule["reason_code"] = reason
    return rule


# (nome, sobrescritas da politica, papel, acao, campo, contexto, canal, decisao, reason_code)
def policy_behaviors(base):
    return [
        ("broker-without-context", {}, "broker", "read", "address.street", {}, None,
         "deny", "default_decision"),
        ("broker-condition-false", {}, "broker", "read", "address.street", {"broker_is_assigned": False}, None,
         "deny", "default_decision"),
        ("public-cannot-read-street", {}, "public", "read", "address.street", None, None,
         "deny", "default_decision"),
        ("director-write-denied", {}, "director", "write", "owner.tax_id", None, None,
         "deny", "default_decision"),
        ("portal-export-number-denied", {}, "portal", "export", "address.number", None, None,
         "deny", "sensitive_field_default_deny"),
        ("prefix-covers-child", {"rules": [_rule("deny", ["read"], ["address"], reason="addr_deny")]},
         "public", "read", "address.number", None, None, "deny", "addr_deny"),
        ("prefix-requires-dot", {"rules": [_rule("deny", ["read"], ["address"], reason="addr_deny")]},
         "public", "read", "addressing", None, None, "deny", "default_decision"),
        ("empty-fields-cover-all", {"rules": [_rule("allow", ["read"], [], roles=["admin"], reason="admin_all")]},
         "admin", "read", "headline", None, None, "allow", "admin_all"),
        ("empty-roles-cover-any", {"rules": [_rule("allow", ["read"], ["headline"], reason="any_role")]},
         "stranger", "read", "headline", None, None, "allow", "any_role"),
        ("priority-beats-deny",
         {"rules": [_rule("deny", ["read"], ["headline"], priority=0, reason="low_deny"),
                    _rule("allow", ["read"], ["headline"], priority=5, reason="hi_allow")]},
         "public", "read", "headline", None, None, "allow", "hi_allow"),
        ("tie-deny-wins",
         {"rules": [_rule("allow", ["read"], ["headline"], priority=5, reason="tie_allow"),
                    _rule("deny", ["read"], ["headline"], priority=5, reason="tie_deny")]},
         "public", "read", "headline", None, None, "deny", "tie_deny"),
        ("needs-approval-on-export",
         {"rules": [_rule("allow", ["export"], ["headline"], roles=["portal"], reason="portal_export")],
          "requires_approval_for": ["export"]},
         "portal", "export", "headline", None, None, "needs_approval", "portal_export"),
        ("default-allow-nonsensitive-read", {"default_decision": "allow", "rules": []},
         "public", "read", "headline", None, None, "allow", "default_decision"),
        ("default-allow-sensitive-read", {"default_decision": "allow", "rules": []},
         "public", "read", "owner.tax_id", None, None, "deny", "sensitive_field_default_deny"),
        ("default-allow-export", {"default_decision": "allow", "rules": []},
         "public", "export", "headline", None, None, "deny", "restricted_action_default_deny"),
        ("default-needs-approval", {"default_decision": "needs_approval", "rules": []},
         "public", "read", "headline", None, None, "needs_approval", "default_decision"),
        ("channel-not-allowed",
         {"allowed_channels": ["crm"], "rules": [_rule("allow", ["read"], ["headline"], reason="ok_allow")]},
         "public", "read", "headline", None, "website", "deny", "channel_not_allowed"),
        ("channel-allowed",
         {"allowed_channels": ["crm"], "rules": [_rule("allow", ["read"], ["headline"], reason="ok_allow")]},
         "public", "read", "headline", None, "crm", "allow", "ok_allow"),
        ("rule-without-reason-code", {"rules": [_rule("allow", ["read"], ["headline"])]},
         "public", "read", "headline", None, None, "allow", "rule_allow"),
    ]


# --------------------------------------------------------------------------
# Execucao
# --------------------------------------------------------------------------

class Run(object):
    def __init__(self, root, now):
        self.root = root
        self.now = now
        self.cases = []
        self.observed = {}
        self.warnings = []

    def absorb(self, case_id, notes):
        for note in notes:
            bucket = self.observed.setdefault(note["amb"], [])
            if len(bucket) < 3:
                bucket.append("%s %s" % (case_id, note["path"]))

    def absorb_ids(self, case_id, amb_ids):
        self.absorb(case_id, [{"amb": a, "path": "-", "message": ""} for a in amb_ids])

    def add(self, entity, kind, case_id, source, expected, actual, ok, detail="", codes=None):
        self.cases.append({
            "entity": entity, "kind": kind, "id": case_id, "source": source,
            "expected": expected, "actual": actual, "ok": bool(ok),
            "detail": detail, "codes": codes or [],
        })

    def guarded(self, entity, kind, case_id, source, expected, func):
        try:
            func()
        except Exception as exc:  # defensivo: um defeito do consumidor vira FAIL visivel
            self.add(entity, kind, case_id, source, expected, "internal-error", False,
                     "%s: %s" % (type(exc).__name__, exc))


def _verdict(ctx):
    return "invalid" if ctx.errors else "valid"


def _codes(ctx):
    return ["%s@%s" % (e["code"], e["path"]) for e in ctx.errors]


def validate_case(run, entity, kind, case_id, source, doc, expected, expect_pairs=None):
    ctx = Ctx()
    VALIDATORS[entity](doc, ctx)
    run.absorb(case_id, ctx.notes)
    actual = _verdict(ctx)
    ok = actual == expected
    detail = ""
    if ok and expected == "invalid" and expect_pairs:
        missing = [pair for pair in expect_pairs if pair not in ctx.pairs()]
        if missing:
            ok = False
            detail = "rejeitado por outro motivo; faltou %s" % (missing,)
    if not ok and not detail:
        detail = "; ".join(_codes(ctx)) or "sem erros"
    run.add(entity, kind, case_id, source, expected, actual, ok, detail, _codes(ctx))
    return ctx


def load_published(run):
    """Descobre os exemplos publicados por schema_ref, sem lista fixa de nomes."""
    found = []
    golden = run.root / "tests" / "golden"
    for path in sorted(golden.glob("*.json")):
        try:
            data = load_json(path)
        except (ValueError, OSError) as exc:
            run.warnings.append("ilegivel: %s (%s)" % (path.name, exc))
            continue
        if isinstance(data, dict) and data.get("schema_ref") in ENTITY_BY_REF:
            found.append((path, data))
    return found


PUBLISHED_EXPECT_PAIRS = {
    "property-invalid-money-brl-scalar": [("money_scalar_field", "$.asking_price_brl")],
}


def run_published(run):
    state = {"property": None, "listing": None, "exposure_policy": None}
    for path, data in load_published(run):
        entity = ENTITY_BY_REF[data["schema_ref"]]
        case_id = str(data.get("id", path.name))
        source = "tests/golden/%s" % path.name
        expected = data.get("expected_result")
        if "payload" not in data or expected not in ("valid", "invalid"):
            run.add(entity, "published", case_id, source, str(expected), "bad-fixture", False,
                    "fixture sem payload ou sem expected_result valido")
            continue
        payload = data["payload"]

        def work(entity=entity, case_id=case_id, source=source, expected=expected, payload=payload, data=data):
            ctx = validate_case(run, entity, "published", case_id, source, payload, expected,
                                PUBLISHED_EXPECT_PAIRS.get(case_id))
            if expected == "valid" and not ctx.errors and state.get(entity) is None and entity in state:
                state[entity] = payload
            if expected == "valid" and not ctx.errors:
                follow_up(run, entity, case_id, source, payload, data)

        run.guarded(entity, "published", case_id, source, expected, work)

    sample_path = run.root / "examples" / "property.sample.json"
    if sample_path.exists():
        def sample_work():
            payload = load_json(sample_path)
            validate_case(run, "property", "published", "examples/property.sample.json",
                          "examples/property.sample.json", payload, "valid")
        run.guarded("property", "published", "examples/property.sample.json",
                    "examples/property.sample.json", "valid", sample_work)
    else:
        run.warnings.append("examples/property.sample.json ausente")
    return state


def follow_up(run, entity, case_id, source, payload, data):
    """Resultados publicados adicionais do proprio exemplo (valores, projecao, decisoes)."""
    if entity == "money" and isinstance(data.get("represents"), str):
        shown = format_money(payload)
        run.add("money", "published", case_id + "/represents", source, data["represents"], shown,
                shown == data["represents"], "" if shown == data["represents"] else "formato divergente")
    if entity == "property":
        run.add("property", "published", case_id + "/summary", source, "summary", "summary", True,
                json.dumps(summarize_property(payload), ensure_ascii=False, sort_keys=True))
    if entity == "listing":
        view, unresolved, notes = project_listing(payload)
        run.absorb_ids(case_id, notes)
        expectation = data.get("projection_expectation")
        if isinstance(expectation, dict):
            mismatches = []
            reproduced = 0
            not_evaluable = []
            for key, expected_value in sorted(expectation.items()):
                if key in view:
                    if view[key] == expected_value:
                        reproduced += 1
                    else:
                        mismatches.append("%s: esperado %r, obtido %r" % (key, expected_value, view[key]))
                else:
                    not_evaluable.append(key)
            if not_evaluable:
                run.absorb_ids(case_id, ["AMB-11"])
            detail = "reproduzidos %d/%d; nao avaliaveis: %s" % (
                reproduced, len(expectation), ", ".join(not_evaluable) or "-")
            if mismatches:
                detail += "; divergencias: " + " | ".join(mismatches)
            run.add("listing", "published", case_id + "/projection", source, "projection", "projection",
                    not mismatches, detail)
        leaks = check_leaks(payload, view)
        run.add("listing", "published", case_id + "/no-leak", source, "no-leak", "no-leak" if not leaks else ",".join(leaks),
                not leaks, "")
    if entity == "exposure_policy":
        expected_decisions = data.get("expected_decisions")
        if isinstance(expected_decisions, list):
            context = assumed_context(payload)
            run.absorb_ids(case_id, ["AMB-14"] if context else [])
            for index, item in enumerate(expected_decisions):
                got = decide(payload, item.get("subject_role"), item.get("action"), item.get("field"), context)
                run.absorb_ids(case_id, got["notes"])
                ok = got["decision"] == item.get("decision") and got["reason_code"] == item.get("reason_code")
                label = "%s/decision[%d] %s %s %s" % (case_id, index, item.get("subject_role"),
                                                      item.get("action"), item.get("field"))
                run.add("exposure_policy", "published", label, source,
                        "%s/%s" % (item.get("decision"), item.get("reason_code")),
                        "%s/%s" % (got["decision"], got["reason_code"]), ok)


def run_cross_reference(run, state):
    prop, listing, policy = state["property"], state["listing"], state["exposure_policy"]
    if not (prop and listing and policy):
        run.warnings.append("nao foi possivel montar o trio imovel/anuncio/exposicao a partir dos exemplos")
        return
    links = {
        "listing.property_id == property.id": listing.get("property_id") == prop.get("id"),
        "policy.resource_id == property.id": policy.get("resource_id") == prop.get("id"),
        "listing.transaction_type == property.transaction_type":
            listing.get("transaction_type") == prop.get("transaction_type"),
    }
    broken = [name for name, ok in sorted(links.items()) if not ok]
    run.add("cross_reference", "published", "property-listing-policy-links", "tests/golden/*", "linked",
            "linked" if not broken else "unlinked", not broken, "; ".join(broken))
    level_listing = listing.get("exposure_level")
    level_policy = policy.get("exposure_level")
    if level_listing != level_policy:
        run.absorb_ids("property-listing-policy-links", ["AMB-12"])
    if level_listing in LEVEL_ORDER and level_policy in LEVEL_ORDER:
        effective = max(level_listing, level_policy, key=lambda name: LEVEL_ORDER[name])
        run.add("cross_reference", "published", "effective-exposure-level", "tests/golden/*",
                "confidential", effective, effective == "confidential",
                "listing=%s policy=%s" % (level_listing, level_policy))


def run_index_check(run):
    index_path = run.root / "tests" / "golden" / "conformance-cases.json"
    if not index_path.exists():
        run.warnings.append("indice conformance-cases.json ausente")
        return
    try:
        index = load_json(index_path)
    except (ValueError, OSError) as exc:
        run.warnings.append("indice ilegivel: %s" % exc)
        return
    processed = {}
    for case in run.cases:
        if case["kind"] == "published" and case["source"].startswith("tests/golden/") and "/" not in case["id"]:
            processed[case["source"]] = case
    for entry in index if isinstance(index, list) else []:
        path = entry.get("fixture_path", "")
        mine = processed.get(path)
        if mine is None:
            continue
        ok = entry.get("expected_result") == mine["expected"]
        run.add("index", "published", entry.get("id", path), "tests/golden/conformance-cases.json",
                str(entry.get("expected_result")), mine["expected"], ok,
                "" if ok else "indice e fixture divergem em expected_result")


def run_derived(run, state):
    base_property = state.get("property")
    base_listing = state.get("listing")
    base_policy = state.get("exposure_policy")

    def mutated(base, mutation):
        doc = copy.deepcopy(base)
        mutation(doc)
        return doc

    if base_property:
        for name, mutation, pairs in PROPERTY_NEGATIVES:
            case_id = "property/" + name
            run.guarded("property", "derived", case_id, "mutacao de property.valid", "invalid",
                        lambda n=case_id, m=mutation, p=pairs: validate_case(
                            run, "property", "derived", n, "mutacao de property.valid",
                            mutated(base_property, m), "invalid", p))
        for name, mutation in PROPERTY_POSITIVES:
            case_id = "property/" + name
            run.guarded("property", "derived", case_id, "mutacao de property.valid", "valid",
                        lambda n=case_id, m=mutation: validate_case(
                            run, "property", "derived", n, "mutacao de property.valid",
                            mutated(base_property, m), "valid"))
        run.guarded("property", "derived", "property/not-an-object", "literal", "invalid",
                    lambda: validate_case(run, "property", "derived", "property/not-an-object", "literal",
                                          ["x"], "invalid", [("type", "$")]))
    else:
        run.warnings.append("sem exemplo de imovel valido: casos derivados de imovel nao executados")

    if base_listing:
        for name, mutation, pairs in LISTING_NEGATIVES:
            case_id = "listing/" + name
            run.guarded("listing", "derived", case_id, "mutacao de listing.public-masked", "invalid",
                        lambda n=case_id, m=mutation, p=pairs: validate_case(
                            run, "listing", "derived", n, "mutacao de listing.public-masked",
                            mutated(base_listing, m), "invalid", p))
        for name, mutation in LISTING_POSITIVES:
            case_id = "listing/" + name
            run.guarded("listing", "derived", case_id, "mutacao de listing.public-masked", "valid",
                        lambda n=case_id, m=mutation: validate_case(
                            run, "listing", "derived", n, "mutacao de listing.public-masked",
                            mutated(base_listing, m), "valid"))
        run.guarded("listing", "derived", "listing/leaks", "projecao adulterada", "leak", lambda: run_leak_cases(run, base_listing))
        run.guarded("listing", "derived", "listing/eligibility", "elegibilidade", "mixed",
                    lambda: run_eligibility_cases(run, base_listing, base_policy))
    else:
        run.warnings.append("sem exemplo de anuncio valido: casos derivados de anuncio nao executados")

    if base_policy:
        for name, mutation, pairs in POLICY_NEGATIVES:
            case_id = "policy/" + name
            run.guarded("exposure_policy", "derived", case_id, "mutacao de exposure-policy.default-deny", "invalid",
                        lambda n=case_id, m=mutation, p=pairs: validate_case(
                            run, "exposure_policy", "derived", n, "mutacao de exposure-policy.default-deny",
                            mutated(base_policy, m), "invalid", p))
        for name, mutation in POLICY_POSITIVES:
            case_id = "policy/" + name
            run.guarded("exposure_policy", "derived", case_id, "mutacao de exposure-policy.default-deny", "valid",
                        lambda n=case_id, m=mutation: validate_case(
                            run, "exposure_policy", "derived", n, "mutacao de exposure-policy.default-deny",
                            mutated(base_policy, m), "valid"))
        run.guarded("exposure_policy", "derived", "policy/behaviors", "comportamento", "mixed",
                    lambda: run_behavior_cases(run, base_policy))
    else:
        run.warnings.append("sem exemplo de exposicao valido: casos derivados de exposicao nao executados")

    run.guarded("money", "derived", "money/format", "literal", "mixed", lambda: run_money_cases(run))
    run.guarded("json", "derived", "json/strictness", "literal", "rejected", lambda: run_json_cases(run))


def run_behavior_cases(run, base_policy):
    for name, overrides, role, action, field, context, channel, want_decision, want_reason in policy_behaviors(base_policy):
        policy = copy.deepcopy(base_policy)
        policy.update(copy.deepcopy(overrides))
        case_id = "policy/behavior/" + name
        ctx = Ctx()
        validate_policy(policy, ctx)
        if ctx.errors:
            run.add("exposure_policy", "derived", case_id, "comportamento", "%s/%s" % (want_decision, want_reason),
                    "policy-invalid", False, "; ".join(_codes(ctx)))
            continue
        got = decide(policy, role, action, field, context, channel)
        run.absorb_ids(case_id, got["notes"])
        ok = got["decision"] == want_decision and got["reason_code"] == want_reason
        run.add("exposure_policy", "derived", case_id, "comportamento",
                "%s/%s" % (want_decision, want_reason), "%s/%s" % (got["decision"], got["reason_code"]), ok)


def run_leak_cases(run, base_listing):
    clean_view, _, _ = project_listing(base_listing)
    cases = [
        ("clean-projection", base_listing, clean_view, []),
    ]
    leak_price = dict(clean_view)
    leak_price["price"] = "R$ 17.500.000,00"
    cases.append(("price-shown-when-on-request", base_listing, leak_price, ["price_leak"]))
    leak_number = dict(clean_view)
    leak_number["address.number"] = "1234"
    cases.append(("number-shown-when-approximate", base_listing, leak_number, ["address_leak"]))
    hidden = copy.deepcopy(base_listing)
    hidden["address_display"] = "hidden"
    hidden_view, _, _ = project_listing(hidden)
    leak_hood = dict(hidden_view)
    leak_hood["neighborhood"] = "Itaim Bibi"
    cases.append(("neighborhood-shown-when-hidden", hidden, leak_hood, ["address_leak"]))
    leak_pii = dict(clean_view)
    leak_pii["owner.tax_id"] = "123.456.789-00"
    cases.append(("tax-id-in-view", base_listing, leak_pii, ["pii_leak"]))
    visible = copy.deepcopy(base_listing)
    visible["price_display"] = "visible"
    visible["display_price"] = {"amount": 1750000000, "currency": "BRL"}
    visible_view, _, _ = project_listing(visible)
    cases.append(("visible-price-is-allowed", visible, visible_view, []))
    for name, listing, view, want in cases:
        got = check_leaks(listing, view)
        run.add("listing", "derived", "listing/leak/" + name, "projecao adulterada", ",".join(want) or "none",
                ",".join(got) or "none", got == want)
    en_listing = copy.deepcopy(base_listing)
    en_listing["locale"] = "en-US"
    en_view, _, notes = project_listing(en_listing)
    run.absorb_ids("listing/locale-en-US", notes)
    run.add("listing", "derived", "listing/projection/non-pt-label", "mutacao de locale", ON_REQUEST_TOKEN,
            str(en_view.get("price")), en_view.get("price") == ON_REQUEST_TOKEN)
    hidden_view2, _, _ = project_listing(hidden)
    ok = hidden_view2.get("address.street") is None and hidden_view2.get("neighborhood") is None
    run.add("listing", "derived", "listing/projection/hidden-masks-all", "mutacao de address_display", "masked",
            "masked" if ok else "exposed", ok)


def run_eligibility_cases(run, base_listing, base_policy):
    now = run.now
    past = _iso(now - timedelta(days=1))
    future = _iso(now + timedelta(days=30))
    public = _set(("exposure_level",), "public")
    table = [
        ("eligible-baseline", public, True, False, []),
        ("not-yet-expired", _all(public, _set(("expires_at",), future)), True, False, []),
        ("fixture-as-published-is-restricted", _all(), True, False, ["exposure_level_not_public"]),
        ("paused", _all(public, _set(("listing_status",), "paused")), True, False, ["listing_not_published"]),
        ("record-archived", _all(public, _set(("audit", "record_state"), "archived")), True, False, ["record_not_active"]),
        ("expired", _all(public, _set(("expires_at",), past)), True, False, ["listing_expired"]),
        ("channel-inactive", public, False, False, ["channel_inactive_or_unknown"]),
        ("channel-unknown", public, None, False, ["channel_inactive_or_unknown"]),
        ("level-omitted", _del(("exposure_level",)), True, False, ["exposure_level_not_public"]),
        ("policy-more-restrictive", public, True, True, ["policy_exposure_level_not_public"]),
    ]
    for name, mutation, channel_active, use_policy, want in table:
        listing = copy.deepcopy(base_listing)
        mutation(listing)
        policy = base_policy if use_policy else None
        if use_policy and policy is None:
            run.warnings.append("elegibilidade/%s ignorado: sem exemplo de exposicao" % name)
            continue
        reasons = public_eligibility(listing, now, channel_active, policy)
        if use_policy:
            run.absorb_ids("listing/eligibility/" + name, ["AMB-12"])
        if not want:
            ok = reasons == []
        else:
            ok = all(item in reasons for item in want)
        run.add("listing", "derived", "listing/eligibility/" + name, "elegibilidade",
                "eligible" if not want else "not_eligible:" + ",".join(want),
                "eligible" if not reasons else "not_eligible:" + ",".join(reasons), ok)


def run_money_cases(run):
    table = [
        ({"amount": 1, "currency": "BRL"}, "R$ 0,01"),
        ({"amount": 123456, "currency": "BRL"}, "R$ 1.234,56"),
        ({"amount": 250, "currency": "USD"}, "USD 2.50"),
        ({"amount": -5, "currency": "BRL"}, "-R$ 0,05"),
    ]
    for money, want in table:
        got = format_money(money)
        run.add("money", "derived", "money/format/%s%s" % (money["currency"], money["amount"]), "literal",
                want, got, got == want)


def run_json_cases(run):
    table = [
        ("duplicate-key", '{"id": "a", "id": "b"}'),
        ("nan-literal", '{"amount": NaN}'),
        ("infinity-literal", '{"amount": Infinity}'),
        ("trailing-garbage", '{"a": 1} x'),
    ]
    for name, text in table:
        try:
            load_json_text(text)
            actual = "accepted"
        except ValueError:
            actual = "rejected"
        run.absorb_ids("json/" + name, ["AMB-20"])
        run.add("json", "derived", "json/strict/" + name, "literal", "rejected", actual, actual == "rejected")


# --------------------------------------------------------------------------
# Confronto de deriva com o schema publicado (somente dados)
# --------------------------------------------------------------------------

def schema_drift(root):
    path = root / "schema" / "mbras.schema.json"
    if not path.exists():
        return {"status": "skipped", "reason": "schema/mbras.schema.json ausente", "items": []}
    try:
        schema = load_json(path)
    except (ValueError, OSError) as exc:
        return {"status": "skipped", "reason": "schema ilegivel: %s" % exc, "items": []}
    defs = schema.get("$defs", {}) if isinstance(schema, dict) else {}
    items = []
    for name, mine in sorted(ENUMS.items()):
        published = defs.get(name)
        if not isinstance(published, dict) or "enum" not in published:
            items.append("%s: enum ausente no schema" % name)
            continue
        theirs = tuple(published["enum"])
        if set(theirs) != set(mine):
            items.append("%s: schema-so=%s consumidor-so=%s" % (
                name, sorted(set(theirs) - set(mine)), sorted(set(mine) - set(theirs))))
    for name, spec in sorted(SPEC_BY_DEF.items()):
        published = defs.get(name)
        if not isinstance(published, dict):
            items.append("%s: definicao ausente no schema" % name)
            continue
        if set(published.get("required", [])) != set(spec.required):
            items.append("%s: required schema=%s consumidor=%s" % (
                name, sorted(published.get("required", [])), sorted(spec.required)))
        theirs_props = set((published.get("properties") or {}).keys())
        if theirs_props != set(spec.props.keys()):
            items.append("%s: propriedades schema-so=%s consumidor-so=%s" % (
                name, sorted(theirs_props - set(spec.props.keys())), sorted(set(spec.props.keys()) - theirs_props)))
    return {"status": "ok" if not items else "drift", "reason": "", "items": items}


# --------------------------------------------------------------------------
# Relatorio
# --------------------------------------------------------------------------

def build_report(run, drift):
    failures = [c for c in run.cases if not c["ok"]]
    published = [c for c in run.cases if c["kind"] == "published"]
    derived = [c for c in run.cases if c["kind"] == "derived"]
    register = []
    for amb_id, topic, interpretation in AMBIGUITIES:
        evidence = run.observed.get(amb_id, [])
        register.append({"id": amb_id, "topic": topic, "interpretation": interpretation,
                         "exercised": bool(evidence), "evidence": evidence})
    summary = {
        "published_total": len(published),
        "published_failed": len([c for c in published if not c["ok"]]),
        "derived_total": len(derived),
        "derived_failed": len([c for c in derived if not c["ok"]]),
        "schema_drift_items": len(drift["items"]),
        "warnings": len(run.warnings),
    }
    summary["failures"] = summary["published_failed"] + summary["derived_failed"] + summary["schema_drift_items"]
    summary["result"] = "PASS" if summary["failures"] == 0 else "FAIL"
    return {
        "tool": "independent_consumer",
        "root": str(run.root),
        "now": _iso(run.now),
        "summary": summary,
        "cases": run.cases,
        "schema_drift": drift,
        "ambiguities": register,
        "warnings": run.warnings,
        "failures": failures,
    }


def render_text(report, verbose):
    lines = []
    out = lines.append
    out("PIBRAS independent consumer (A10) - stdlib only")
    out("root: %s" % report["root"])
    out("now : %s" % report["now"])
    out("")
    out("== Exemplos publicados ==")
    for case in report["cases"]:
        if case["kind"] != "published":
            continue
        mark = "PASS" if case["ok"] else "FAIL"
        out("  %s  %-15s %s  esperado=%s obtido=%s" % (mark, case["entity"], case["id"], case["expected"], case["actual"]))
        if case["detail"] and (verbose or not case["ok"] or case["id"].endswith("/projection")):
            out("        %s" % case["detail"])
    derived = [c for c in report["cases"] if c["kind"] == "derived"]
    out("")
    out("== Casos derivados (mutacoes em memoria) ==")
    by_entity = {}
    for case in derived:
        stats = by_entity.setdefault(case["entity"], [0, 0])
        stats[0] += 1
        if not case["ok"]:
            stats[1] += 1
    for entity in sorted(by_entity):
        out("  %-15s executados=%d falhas=%d" % (entity, by_entity[entity][0], by_entity[entity][1]))
    for case in derived:
        if verbose or not case["ok"]:
            mark = "PASS" if case["ok"] else "FAIL"
            out("  %s  %-15s %s  esperado=%s obtido=%s" % (mark, case["entity"], case["id"], case["expected"], case["actual"]))
            if case["detail"] and not case["ok"]:
                out("        %s" % case["detail"])
    out("")
    drift = report["schema_drift"]
    out("== Confronto com o schema publicado (somente dados) ==")
    if drift["status"] == "skipped":
        out("  ignorado: %s" % drift["reason"])
    elif drift["items"]:
        for item in drift["items"]:
            out("  DERIVA  %s" % item)
    else:
        out("  sem deriva em enums, campos obrigatorios e propriedades das definicoes cobertas")
    out("")
    out("== Interpretacoes ambiguas (registro do consumidor) ==")
    for entry in report["ambiguities"]:
        flag = "exercitada" if entry["exercised"] else "so documentada"
        out("  %s [%s] %s" % (entry["id"], flag, entry["topic"]))
        if verbose:
            out("        %s" % entry["interpretation"])
            for ev in entry["evidence"]:
                out("        evidencia: %s" % ev)
    if report["warnings"]:
        out("")
        out("== Avisos ==")
        for warning in report["warnings"]:
            out("  %s" % warning)
    s = report["summary"]
    out("")
    out("Resumo: publicados %d (falhas %d) | derivados %d (falhas %d) | deriva de schema %d | avisos %d"
        % (s["published_total"], s["published_failed"], s["derived_total"], s["derived_failed"],
           s["schema_drift_items"], s["warnings"]))
    out("Resultado: %s" % s["result"])
    return "\n".join(lines)


def execute(root, now, crosscheck=True):
    run = Run(root, now)
    state = run_published(run)
    run_cross_reference(run, state)
    run_derived(run, state)
    run_index_check(run)
    drift = schema_drift(root) if crosscheck else {"status": "skipped", "reason": "desativado", "items": []}
    return build_report(run, drift)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Consumidor independente PIBRAS v0.2 (imovel, anuncio, exposicao).")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="raiz do repositorio (padrao: pai de scripts/)")
    parser.add_argument("--now", help="instante de referencia RFC 3339 (padrao: agora, UTC)")
    parser.add_argument("--json", action="store_true", help="emite o relatorio completo em JSON")
    parser.add_argument("-v", "--verbose", action="store_true", help="lista todos os casos e as interpretacoes")
    parser.add_argument("--no-schema-crosscheck", action="store_true", help="nao confronta com schema/mbras.schema.json")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not (root / "tests" / "golden").is_dir():
        sys.stderr.write("erro: %s nao contem tests/golden\n" % root)
        return 2
    now = _parse_dt(args.now) if args.now else datetime.now(timezone.utc)
    if now is None:
        sys.stderr.write("erro: --now deve ser RFC 3339, ex.: 2026-11-25T00:00:00Z\n")
        return 2

    report = execute(root, now, crosscheck=not args.no_schema_crosscheck)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(render_text(report, args.verbose) + "\n")
    return 0 if report["summary"]["failures"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
