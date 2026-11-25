"""Reference conversion of validated JSON records; never writes to a database."""
from copy import deepcopy
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5


LEGACY_ONLY = {"preferred_contact", "marketing_consent", "notes"}


def migrate(owners, links, parties, ownerships, property_evidence):
    """Return canonical records and a private receipt for the legacy projection.

    links contains flattened Property.owners entries plus the parent property_id.
    property_evidence supplies the actual parent stamps, not invented timestamps.
    Input is one isolated tenant/source scope; entity schemas are a prerequisite.
    """
    parties, ownerships = deepcopy(parties), deepcopy(ownerships)
    by_party = {p["id"]: p for p in parties}
    by_id = {o["id"]: o for o in ownerships}
    if len(by_party) != len(parties) or len(by_id) != len(ownerships):
        raise ValueError("duplicate-id")
    receipt = {"owners": [], "links": []}
    seen_owners, seen_links = set(), set()
    for owner in owners:
        pid = owner["id"]
        if pid in seen_owners:
            raise ValueError("duplicate-owner")
        seen_owners.add(pid)
        party = {k: deepcopy(v) for k, v in owner.items() if k not in LEGACY_ONLY | {"owner_type"}}
        party["party_type"] = owner["owner_type"]
        if pid not in by_party:
            parties.append(party)
            by_party[pid] = party
        elif any(k not in by_party[pid] or v != by_party[pid][k] for k, v in party.items()):
            raise ValueError("party-conflict")
        receipt["owners"].append((pid, list(owner), {k: deepcopy(owner[k]) for k in LEGACY_ONLY & owner.keys()}))
    for link in links:
        prop, pid = link["property_id"], link["owner_id"]
        if (prop, pid) in seen_links:
            raise ValueError("duplicate-link")
        seen_links.add((prop, pid))
        if pid not in by_party or prop not in property_evidence:
            raise ValueError("missing-reference")
        stamps = property_evidence[prop]
        target = {k: deepcopy(v) for k, v in link.items() if k != "owner_id"}
        target.update(party_id=pid, provenance=deepcopy(stamps["provenance"]), audit=deepcopy(stamps["audit"]))
        matches = [o for o in ownerships if (o.get("property_id"), o["party_id"]) == (prop, pid)]
        if matches:
            def comparable(o):
                return (o.get("owner_role", "owner"), o.get("is_primary", False), o.get("ownership_pct"),
                        o.get("starts_at"), o.get("ends_at"), o["provenance"], o["audit"])
            if len(matches) != 1 or comparable(matches[0]) != comparable(target):
                raise ValueError("link-conflict")
            oid = matches[0]["id"]
        else:
            oid = str(uuid5(NAMESPACE_URL, f"urn:pibras:compat:property_owners:{prop}:{pid}"))
            if oid in by_id:
                raise ValueError("link-id-collision")
            target["id"] = oid
            by_id[oid] = target
            ownerships.append(target)
        receipt["links"].append((oid, list(link)))
    totals = {}
    for o in ownerships:
        axes = [(k, o[k]) for k in ("property_id", "unit_id") if o.get(k) is not None]
        if len(axes) != 1 or o["party_id"] not in by_party:
            raise ValueError("invalid-target")
        if o["audit"]["record_state"] == "active" and o.get("owner_role", "owner") == "owner":
            key = axes[0]
            pct = o.get("ownership_pct")
            totals[key] = totals.get(key, Decimal(0)) + Decimal(str(pct if pct is not None else 0))
            if totals[key] > 100:
                raise ValueError("aggregate-ownership")
    return parties, ownerships, receipt


def restore_legacy(parties, ownerships, receipt):
    """Recreate originating JSON rows only; do not flatten canonical-only links."""
    people = {p["id"]: p for p in parties}
    edges = {o["id"]: o for o in ownerships}
    owners, links = [], []
    for pid, fields, private in receipt["owners"]:
        p = people[pid]
        row = {**p, "owner_type": p["party_type"], **private}
        owners.append({k: row[k] for k in fields})
    for oid, fields in receipt["links"]:
        o = edges[oid]
        row = {"ownership_pct": None, "owner_role": "owner", "is_primary": False, **o, "owner_id": o["party_id"]}
        links.append({k: row[k] for k in fields})
    return owners, links


def check_corpus(corpus):
    """Execute manifest expectations; identify the failing scenario without dumping PII."""
    entities = corpus["entities"]
    cases = corpus["cases"]
    required = {"legacy", "canonical", "mixed", "coownership", "identity-conflict", "link-conflict"}
    failures = [f"missing scenario: {name}" for name in sorted(required - {case["name"] for case in cases})]
    for case in cases:
        def rows(key):
            return [entities[k] for k in case[key]]
        args = [rows(k) for k in ("owners", "links", "parties", "ownerships")]
        evidence = {entities["propertyA"]: entities["propertyEvidence"]}
        try:
            parties, edges, receipt = migrate(*args, evidence)
        except ValueError as exc:
            if str(exc) != case.get("reject"):
                failures.append(f"{case['name']}: unexpected rejection {exc}")
            continue
        if "reject" in case:
            failures.append(f"{case['name']}: expected rejection {case['reject']}")
        elif parties != rows("expected_parties") or edges != rows("expected_ownerships"):
            failures.append(f"{case['name']}: canonical records differ")
        elif restore_legacy(parties, edges, receipt) != (args[0], args[1]):
            failures.append(f"{case['name']}: legacy round-trip differs")
        elif migrate(*args[:2], parties, edges, evidence) != (parties, edges, receipt):
            failures.append(f"{case['name']}: repeated import differs")
    return failures
