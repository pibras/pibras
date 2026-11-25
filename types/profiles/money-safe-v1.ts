import { z } from "zod";
import { Money } from "../mbras.ts";

export const SafeMoney = Money.extend({
  amount: Money.shape.amount.min(Number.MIN_SAFE_INTEGER).max(Number.MAX_SAFE_INTEGER),
});

// JSON.parse's reviver supplies the original numeric token (Node 22+).
// Never use the already-rounded reviver value to decide integrality or bounds.
function exactCents(token: string): number {
  const [mantissa = "", exponent = "0"] = token.toLowerCase().split("e");
  const [whole = "", fraction = ""] = mantissa.replace(/^-/, "").split(".");
  const digits = (whole + fraction).replace(/^0+/, "");
  if (!digits) return 0;

  // For a nonzero value an exact safe integer has 1..16 integral digits.
  // Extreme exponents fail here, before padding or allocating a BigInt.
  const width = digits.length + Number(exponent) - fraction.length;
  if (width < 1 || width > 16 || /[1-9]/.test(digits.slice(width)))
    throw new RangeError("amount must be an exact safe integer");
  const magnitude = BigInt(digits.slice(0, width).padEnd(width, "0"));
  if (magnitude > 9007199254740991n) throw new RangeError("amount outside money-safe-v1");
  return Number(mantissa.startsWith("-") ? -magnitude : magnitude);
}

/** Wire entry point. SafeMoney alone validates only already-materialized objects. */
export function parseSafeMoneyJson(raw: string): z.output<typeof SafeMoney> {
  const obj: unknown = JSON.parse(raw, (key: string, value: unknown, context?: { source?: string }) => {
    if (key !== "amount" || typeof value !== "number") return value;
    if (typeof context?.source !== "string") throw new TypeError("raw JSON number source required");
    return exactCents(context.source);
  });
  return SafeMoney.parse(obj);
}

const SettlementTotal = SafeMoney.extend({ amount: SafeMoney.shape.amount.nonnegative() });
const Share = z.object({
  bps: z.int().min(0).max(10_000),
  remainder_priority: z.int(),
}).strict();

/** Largest remainder v1. Lower priority number wins ties. Output follows input order. */
export function allocateSettlement(total: z.input<typeof SafeMoney>, shares: z.input<typeof Share>[]) {
  const { amount, currency } = SettlementTotal.parse(total);
  const lines = z.array(Share).nonempty().parse(shares);
  if (new Set(lines.map(line => line.remainder_priority)).size !== lines.length)
    throw new RangeError("remainder_priority must be unique");
  if (lines.reduce((sum, line) => sum + line.bps, 0) !== 10_000)
    throw new RangeError("settlement requires 10000 bps");

  const allocations = lines.map(({ bps, remainder_priority }) => {
    const product = BigInt(amount) * BigInt(bps);
    return { cents: product / 10_000n, remainder: product % 10_000n, remainder_priority };
  });
  const remaining = BigInt(amount) - allocations.reduce((sum, line) => sum + line.cents, 0n);
  const ranked = [...allocations].sort((a, b) =>
    Number(b.remainder - a.remainder) || a.remainder_priority - b.remainder_priority);
  for (const line of ranked.slice(0, Number(remaining))) line.cents++;
  return allocations.map(({ cents }) => ({ amount: Number(cents), currency }));
}
