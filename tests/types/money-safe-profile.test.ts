import { strict as assert } from "node:assert";
import { test } from "node:test";
import { allocateSettlement } from "../../types/profiles/money-safe-v1.ts";

const total = { amount: Number.MAX_SAFE_INTEGER, currency: "BRL" as const };
const share = (bps: number, remainder_priority: number) => ({ bps, remainder_priority });

test("settlement preserves exact cents at the ceiling with unequal remainders", () => {
  const lines = allocateSettlement(total, [share(3333, 0), share(3333, 1), share(3334, 2)]);
  assert.deepEqual(lines.map(line => line.amount), [3002099511605172, 3002099511605172, 3003000231530647]);
  assert.ok(lines.every(line => line.currency === total.currency));
  assert.equal(lines.reduce((sum, line) => sum + BigInt(line.amount), 0n), BigInt(total.amount));
});

test("ties use ascending priority and preserve input order; zero settles exactly", () => {
  const halves = [share(5000, 9), share(5000, 1)];
  assert.deepEqual(allocateSettlement(total, halves).map(x => x.amount), [4503599627370495, 4503599627370496]);
  assert.deepEqual(allocateSettlement({ ...total, amount: 0 }, halves).map(x => x.amount), [0, 0]);
});

test("invalid totals, weights and ambiguous priorities are rejected", () => {
  for (const amount of [-1, 0.5, total.amount + 1])
    assert.throws(() => allocateSettlement({ ...total, amount }, [share(10000, 0)]));
  for (const lines of [[], [share(9999, 0)], [share(-1, 0), share(10001, 1)],
    [share(5000, 0), share(5000, 0)], [share(9999.5, 0), share(0.5, 1)]])
    assert.throws(() => allocateSettlement(total, lines));
});
