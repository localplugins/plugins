---
description: Fetch version-matched documentation for a library used in this project and ground an answer in it (optionally narrowed to a topic).
argument-hint: <library> [topic]
---

# /docs

Explicit pull of version-matched documentation for `$ARGUMENTS`. The first
token is the `<library>` name; anything after it is an optional `[topic]`
that narrows the fetch (e.g. a specific method, option, or concept).

Run the same resolve → fetch → ground loop the `docpin` skill uses — see
`skills/docpin/SKILL.md` for the overview and `skills/docpin/references/resolver.md`
for the full algorithm. Do not restate the loop here; follow it:

1. **Detect ecosystem** — find the lockfile/manifest nearest the current
   project (or workspace, in a monorepo) that references `<library>`.
   Consult the precedence table in `references/resolver.md` §1. If the
   library isn't found in any lockfile/manifest, it isn't installed in this
   project — skip to the "not installed" case below.
2. **Resolve the installed version** — prefer the locked version from a
   lockfile; fall back to resolving a manifest range via the registry
   (label as inferred, per `references/resolver.md` §2).
3. **Registry lookup + fetch version-pinned docs** — per the ecosystem's
   recipe (`references/ecosystem-npm.md`, `ecosystem-pypi.md`,
   `ecosystem-crates.md`, or `ecosystem-go.md`), fetch the doc source for
   that exact version. If `[topic]` was given, narrow the fetch/extraction
   to that topic; otherwise fetch the general docs entry point.
4. **Distill + ground** — apply `references/output-contract.md`: extract
   only what's relevant to `[topic]` (or a general overview if no topic was
   given), never fabricate a symbol absent from the resolved version's
   docs, and end the answer with a `Source:` line naming the resolved
   `<pkg>@<version>` and the exact URL(s) fetched.

## If the library isn't installed in this project

Resolve the **latest** published version from the registry instead, and
label the version basis explicitly as `latest (unpinned)` (the canonical
label from `references/output-contract.md` §4) — do not present it as if it
were a version-pinned match for this project.

## If a cached entry exists

Check `.docpin/cache/<ecosystem>/<pkg>@<version>[/topic].md` first, per
`references/caching.md` — reuse a hit instead of re-fetching, and cite it
exactly as if freshly fetched.
