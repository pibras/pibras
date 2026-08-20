#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "==3.13.9"
# dependencies = []
# ///

"""Project a governed PIBRAS public record into schema.org JSON-LD.

Source of truth is the `property_public` view (see db/schema.sql), never
`property`, `unit` or `property_full`. Restricted fields (matricula, exact
coordinates, internal scores) are absent from the input by construction, so
this exporter cannot leak them even if asked to.

Vocabulary: schema.org V30.0 (2026-03-19), retrieved 2026-07-26.
Field-by-field rationale and loss classification: mappings/schema-org-to-pibras.md

Usage:
    uv run scripts/export_schema_org.py --input <record.json>
    uv run scripts/export_schema_org.py --input <record.json> --round-trip
"""

from __future__ import annotations

import argparse
import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Final

SCHEMA_ORG_VERSION: Final = "V30.0"
SCHEMA_ORG_RETRIEVED: Final = "2026-07-26"
GR: Final = "http://purl.org/goodrelations/v1#"

# Columns of the governed public surface. Anything outside this set is a
# programming error: it means the caller read from an ungoverned source.
PUBLIC_SURFACE: Final = frozenset(
    {
        "id", "code", "transaction_type", "property_status", "availability",
        "asking_price_amount", "asking_price_currency", "property_type",
        "usable_area_m2", "total_area_m2", "bedrooms", "suites", "bathrooms",
        "parking_spaces", "sun_orientation", "view_type", "city", "state",
        "neighborhood_id", "latitude_approx", "longitude_approx",
        "building_name", "amenities", "updated_at",
    }
)

# Fields that must never appear in input. Presence means the record came from
# property_full or a raw table, which is a governance failure, not a mapping bug.
FORBIDDEN_FIELDS: Final = frozenset(
    {
        "matricula", "latitude", "longitude", "liquidity_score", "match_score",
        "rarity_score", "off_market_potential", "owner", "owner_id",
        "addr_street", "addr_number", "documents",
    }
)

ACCOMMODATION_TYPE: Final = {
    "apartment": "Apartment", "penthouse": "Apartment", "studio": "Apartment",
    "loft": "Apartment", "flat": "Apartment",
    "house": "House", "house_condo": "House",
    "land": "Accommodation", "farm": "Accommodation",
    "commercial_room": "Accommodation", "commercial_building": "Accommodation",
    "warehouse": "Accommodation", "hotel": "Accommodation",
    "whole_building": "Accommodation", "other": "Accommodation",
}

# ItemAvailability members verified at https://schema.org/ItemAvailability
AVAILABILITY: Final = {
    "available": "https://schema.org/InStock",
    "reserved": "https://schema.org/Reserved",
    "under_offer": "https://schema.org/LimitedAvailability",
    "sold": "https://schema.org/SoldOut",
    "rented": "https://schema.org/SoldOut",
    "suspended": "https://schema.org/OutOfStock",
}

# Statuses that must never reach publication. property_public already filters
# them; this is defence in depth.
UNPUBLISHABLE_STATUS: Final = frozenset({"draft", "off_market", "archived"})

# BusinessFunction members verified at https://schema.org/BusinessFunction
BUSINESS_FUNCTION: Final = {
    "sale": [f"{GR}Sell"],
    "rent": [f"{GR}LeaseOut"],
    "sale_rent": [f"{GR}Sell", f"{GR}LeaseOut"],
    "season_rent": [f"{GR}LeaseOut"],
}

# Fields whose PIBRAS value is recoverable from the output without consulting
# the source. Everything else is declared non-round-trippable in the mapping doc.
ROUND_TRIP_FIELDS: Final = frozenset(
    {
        "id", "property_type", "transaction_type", "asking_price_amount",
        "asking_price_currency", "usable_area_m2", "bedrooms", "bathrooms",
        "city", "state", "building_name",
    }
)


class ExportError(Exception):
    """Raised when the input is not a governed public record."""


def price_from_centavos(value: Any) -> str:
    """Serialize integer centavos as an exact schema.org decimal Text value."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ExportError("asking_price_amount must be integer centavos")
    return format(Decimal(value).scaleb(-2), "f")


def centavos_from_price(value: Any) -> int:
    """Recover centavos without introducing binary floating-point arithmetic."""
    if isinstance(value, float):
        raise ValueError("schema.org price must not use binary float")
    try:
        price = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"invalid schema.org price {value!r}") from exc
    centavos = price.scaleb(2)
    if centavos != centavos.to_integral_value():
        raise ValueError(f"schema.org price has sub-cent precision: {value!r}")
    return int(centavos)


def validate_input(record: dict[str, Any]) -> None:
    leaked = sorted(FORBIDDEN_FIELDS & record.keys())
    if leaked:
        raise ExportError(
            "input carries restricted fields "
            f"{leaked}; schema.org export must derive from property_public"
        )
    unknown = sorted(record.keys() - PUBLIC_SURFACE)
    if unknown:
        raise ExportError(f"input has fields outside property_public: {unknown}")
    status = record.get("property_status")
    if status in UNPUBLISHABLE_STATUS:
        raise ExportError(f"property_status={status!r} is not publishable")


def amenity(name: str, value: Any) -> dict[str, Any]:
    return {
        "@type": "LocationFeatureSpecification",
        "name": name,
        "value": value,
    }


def build_accommodation(record: dict[str, Any]) -> dict[str, Any]:
    property_type = record.get("property_type", "other")
    node: dict[str, Any] = {
        "@type": ACCOMMODATION_TYPE.get(property_type, "Accommodation"),
        "identifier": record["id"],
        # Carries the Brazilian type verbatim: this is what makes the lossy
        # @type mapping recoverable.
        "accommodationCategory": property_type,
    }
    if record.get("building_name"):
        node["name"] = record["building_name"]
    if record.get("usable_area_m2") is not None:
        node["floorSize"] = {
            "@type": "QuantitativeValue",
            "value": record["usable_area_m2"],
            "unitCode": "MTK",  # UN/CEFACT: square metre
        }
    for field, prop in (
        ("bedrooms", "numberOfBedrooms"),
        ("bathrooms", "numberOfBathroomsTotal"),
    ):
        if record.get(field) is not None:
            node[prop] = record[field]

    address: dict[str, Any] = {"@type": "PostalAddress", "addressCountry": "BR"}
    if record.get("city"):
        address["addressLocality"] = record["city"]
    if record.get("state"):
        address["addressRegion"] = record["state"]
    node["address"] = address

    lat, lon = record.get("latitude_approx"), record.get("longitude_approx")
    if lat is not None and lon is not None:
        node["geo"] = {"@type": "GeoCoordinates", "latitude": lat, "longitude": lon}

    # Accommodation defines no parking/orientation/view property, so these
    # become named features rather than being silently dropped.
    features: list[dict[str, Any]] = [
        amenity(name, True) for name in record.get("amenities") or []
    ]
    if record.get("parking_spaces") is not None:
        features.append(amenity("parking_spaces", record["parking_spaces"]))
    for field in ("sun_orientation", "view_type"):
        if record.get(field):
            features.append(amenity(field, record[field]))
    if features:
        node["amenityFeature"] = features
    return node


def build_offers(record: dict[str, Any]) -> list[dict[str, Any]]:
    transaction = record.get("transaction_type", "sale")
    availability = AVAILABILITY.get(record.get("property_status", ""))
    offers: list[dict[str, Any]] = []
    for function in BUSINESS_FUNCTION.get(transaction, [f"{GR}Sell"]):
        offer: dict[str, Any] = {"@type": "Offer", "businessFunction": function}
        if availability:
            offer["availability"] = availability
        amount = record.get("asking_price_amount")
        if amount is not None:
            # schema.org accepts Text for price. A decimal string preserves the
            # exact integer-cent amount without passing through binary float.
            offer["price"] = price_from_centavos(amount)
            offer["priceCurrency"] = record.get("asking_price_currency", "BRL")
        offers.append(offer)
    return offers


def export(record: dict[str, Any]) -> dict[str, Any]:
    validate_input(record)
    document: dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "RealEstateListing",
        "mainEntity": build_accommodation(record),
        "offers": build_offers(record),
    }
    if record.get("updated_at"):
        # Approximate: datePosted is publication, updated_at is last change.
        document["datePosted"] = record["updated_at"]
    return document


def round_trip(record: dict[str, Any], document: dict[str, Any]) -> list[str]:
    """Recover PIBRAS values from the output and report semantic mismatches."""
    accommodation = document["mainEntity"]
    offers = document["offers"]
    recovered: dict[str, Any] = {
        "id": accommodation.get("identifier"),
        "property_type": accommodation.get("accommodationCategory"),
        "building_name": accommodation.get("name"),
        "bedrooms": accommodation.get("numberOfBedrooms"),
        "bathrooms": accommodation.get("numberOfBathroomsTotal"),
        "city": accommodation.get("address", {}).get("addressLocality"),
        "state": accommodation.get("address", {}).get("addressRegion"),
    }
    floor_size = accommodation.get("floorSize")
    if floor_size:
        recovered["usable_area_m2"] = floor_size.get("value")

    functions = [offer.get("businessFunction") for offer in offers]
    for name, expected in BUSINESS_FUNCTION.items():
        if functions == expected:
            recovered["transaction_type"] = name
            break

    if offers and "price" in offers[0]:
        try:
            recovered["asking_price_amount"] = centavos_from_price(offers[0]["price"])
        except ValueError as exc:
            recovered["asking_price_amount"] = f"<invalid price: {exc}>"
        recovered["asking_price_currency"] = offers[0].get("priceCurrency")

    mismatches: list[str] = []
    for field in sorted(ROUND_TRIP_FIELDS):
        if field not in record:
            continue
        original, back = record[field], recovered.get(field)
        # season_rent and rent share LeaseOut, so recovery is ambiguous by
        # design; the mapping document declares this loss explicitly.
        if field == "transaction_type" and original == "season_rent" and back == "rent":
            continue
        if original != back:
            mismatches.append(f"{field}: {original!r} -> {back!r}")
    return mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--round-trip", action="store_true")
    parser.add_argument("--expect-failure", action="store_true",
                        help="invert exit code; for negative fixtures")
    args = parser.parse_args()

    payload = json.loads(args.input.read_text(encoding="utf-8"))
    # Conformance fixtures wrap the record so the file's top-level `id` is the
    # case id; a bare public record is also accepted.
    record = payload["record"] if "record" in payload else payload
    try:
        document = export(record)
    except ExportError as exc:
        if args.expect_failure:
            print(f"PASS: rejected as expected: {exc}")
            return 0
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if args.expect_failure:
        print("FAIL: expected rejection but export succeeded", file=sys.stderr)
        return 1

    if args.round_trip:
        mismatches = round_trip(record, document)
        if mismatches:
            print("FAIL: round-trip lost declared-preserved fields:", file=sys.stderr)
            for entry in mismatches:
                print(f"  {entry}", file=sys.stderr)
            return 1
        print(f"PASS: round-trip preserved {len(ROUND_TRIP_FIELDS)} declared fields")
        return 0

    json.dump(document, sys.stdout, indent=2, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
