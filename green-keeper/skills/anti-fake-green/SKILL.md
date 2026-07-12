---
name: anti-fake-green
description: Use whenever fixing a failing test/type error or writing a test, to guarantee the fix is real and not a cheat. Defines what counts as fake-green and how to verify a fix is legitimate.
---

# Anti-Fake-Green

Green must mean the code is actually correct. Making red go green by cheating is worse than leaving it red, because it hides the bug. These rules are non-negotiable.

## Use when

- Fixing a failing test or a type/compile error (as `fixer`).
- Writing or updating a test (as `test-writer`).
- Judging whether a change is a real fix or a cheat (as `green-guardian`).

## The one rule

Change the smallest amount of **production** code (or a genuinely-wrong test) needed to make the check pass **for the right reason** — never suppress the signal.

## Fake-green, at a glance

Reject any change that does one of these instead of fixing the cause:

- **Removes the test** — skip / delete / comment out / `.skip` / `.only` / `xit` / `xdescribe` / `@pytest.mark.skip`.
- **Weakens the assertion** — loosen an expected value, `toEqual` → `toBeTruthy`, delete assertions.
- **Silences the error** — `@ts-ignore`, `eslint-disable`, `# type: ignore`, empty `catch {}`, `except: pass`.
- **Widens the type** — to `any` / `unknown` / `object` just to clear a type error.
- **Pads coverage** — tests that assert nothing or only that a mock was called.
- **Bends the test to the bug** — editing the test to match buggy behavior when the *code* is wrong.

## Decision guide

1. Is production code wrong, or is the test wrong? Fix whichever is genuinely at fault; default to production code.
2. Would this change survive `green-guardian`'s diff inspection? If it matches any fake-green pattern above, it fails — redo it.
3. Can you prove it with revert-verification? If not, you haven't proven green.
4. Can't make it genuinely green? Stop and report exactly what's blocking. Never fake it.

## Deep references

- **`references/fake-green-patterns.md`** — side-by-side fake-green vs. real-fix examples in JS/TS, Python, Go, and Rust, plus the full rejection catalog `green-guardian` applies.
- **`references/revert-verification.md`** — the step-by-step procedure to prove a fix or a new test is real, using `git stash` / file checkout, with commands and pitfalls.
