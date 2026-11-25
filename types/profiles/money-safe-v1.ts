import { z } from "zod";
import { Money } from "../mbras.ts";

export const SafeMoney = Money.extend({
  amount: Money.shape.amount.min(Number.MIN_SAFE_INTEGER).max(Number.MAX_SAFE_INTEGER),
});

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
