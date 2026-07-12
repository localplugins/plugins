---
name: docpin
description: Use when about to write or explain code that imports or calls a third-party library, or when the user asks how to use a named library/framework — resolves the version installed in the project and grounds the answer in version-matched documentation.
---

# docpin

Ground library code in documentation for the *exact version installed in this
project* — not training-data memory, and not merely "latest."

## When to trigger

- Claude is about to write or explain code that imports/calls a **third-party**
  library (npm, PyPI, crates.io, or Go module).
- The user asks how to use a named library or framework ("how do I do X with
  `<lib>`", "why isn't `<lib>.foo()` working", etc.).

## When NOT to trigger

- Standard-library / language-builtin APIs (e.g. Python's `os`, Node's `fs`,
  Rust's `std`, Go's `net/http`) — these aren't version-pinned third-party
  packages and don't need registry resolution.
- Pure algorithm/logic questions with no library API surface involved.
- The project already has a fresh cache hit for this exact `pkg@version` (see
  `references/caching.md`) — reuse it instead of re-fetching.

## The resolve → fetch → ground loop

Five steps, detailed in `references/resolver.md`:

1. **Detect ecosystem** — find the lockfile/manifest nearest the file in
   focus (lockfile takes precedence over manifest).
2. **Resolve installed version** — read the concrete pinned version from the
   lockfile, or infer one from a manifest range via the registry.
3. **Registry lookup** — fetch registry metadata to confirm the version and
   get the repo/docs URLs.
4. **Fetch version-pinned docs** — fetch the actual docs for that exact
   version, per the ecosystem's recipe.
5. **Distill + ground** — extract what's relevant, then write or explain code
   against it, citing the version and URL.

For the full algorithm, the file-precedence table, the registry URLs, and the
fallback chain (no lockfile, 404, private package), read
`references/resolver.md`.

## Honesty invariant

Every grounded answer must:

- **Cite the resolved version and the exact URL(s) fetched**, so the user can
  verify.
- **Never invent a symbol** that isn't present in the resolved version's docs
  — if a requested API isn't there, say so plainly (e.g. "`useFooBar` is not
  in `react@17.0.2`") instead of guessing or fabricating.

This holds even in fallback cases: label *latest*, *closest available
(`<version>`)*, or *local (bundled)* explicitly rather than presenting a
fallback result as an exact version match.

## Further reading

- `references/resolver.md` — the full detection/resolution/fallback algorithm.
- `references/ecosystem-npm.md`, `references/ecosystem-pypi.md`,
  `references/ecosystem-crates.md`, `references/ecosystem-go.md` — per-ecosystem
  lockfile parsing, registry calls, and doc-URL templates.
- `references/output-contract.md` — distillation, citation format, and honesty
  rules for the final answer.
- `references/caching.md` — cache key format and invalidation.

## Delegating to agents

- A heavy single-library fetch (unfamiliar registry, deep topic, multiple
  fallback hops) can be delegated to the `doc-fetcher` agent so the multi-step
  resolve → fetch → distill loop runs in isolation, keeping raw registry JSON
  and fetched pages out of the main session's context.
- Before a grounded answer is trusted for load-bearing code, the
  `citation-guardian` agent can verify it: re-checks the cited version against
  the lockfile, confirms the cited URL resolves and is version-pinned, and
  confirms cited symbols actually appear in that version's docs.
