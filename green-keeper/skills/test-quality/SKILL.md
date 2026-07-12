---
name: test-quality
description: Use when writing or evaluating a test. Defines what makes a test good — behavioral, focused, and actually able to catch a regression.
---

# Test Quality

A good test catches a real regression and reads as a spec of intended behavior. A test that can't fail when the code breaks is worse than no test — it gives false confidence.

## Use when

- Writing or updating a test (as `test-writer`).
- Judging whether a test is worth keeping (as `green-guardian`).

## Decision guide

1. **Assert behavior, not implementation.** Check outputs and observable effects, so refactors don't break the test but bugs do.
2. **Critical path first, then real edge cases** — empty/null inputs, boundaries, error paths, off-by-one. Skip edge cases that can't actually occur.
3. **Narrowest assertion that captures intent** — exact values over "truthy".
4. **Deterministic** — no reliance on time, network, ordering, or randomness without control.
5. **Named for the behavior** — `returns_zero_for_empty_cart`, not `test1`.
6. **One behavior per test** — split so a failure localizes the bug.
7. **Match the project** — its framework, file layout, and naming conventions. Put the test where its neighbors live.

## Avoid

- Tautologies (`expect(x).toBe(x)`) and mock-testing-mocks (asserting only that a mock was called, with no real output check).
- Over-mocking that hides the behavior under test.
- One giant test asserting ten things.
- Snapshot tests as a substitute for meaningful assertions.

Every test you write should pass its revert-verification (see the `anti-fake-green` skill): fail on the pre-change code, pass on the change.

## Deep reference

- **`references/test-patterns.md`** — good-vs-bad test examples across ecosystems: behavioral vs. implementation assertions, edge-case selection, controlling nondeterminism, right-sized mocking, and one-behavior-per-test splits.
