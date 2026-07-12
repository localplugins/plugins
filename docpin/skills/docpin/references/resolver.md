# resolver.md — the core resolve → ground algorithm

This is the deterministic core that every ecosystem recipe plugs into. `SKILL.md`
links here for the full detail; the per-ecosystem recipes (`ecosystem-npm.md`,
`ecosystem-pypi.md`, `ecosystem-crates.md`, `ecosystem-go.md`) fill in the
ecosystem-specific URLs and lockfile parsing referenced below.

## 1. Detect ecosystem

Locate lockfiles/manifests near the file in focus (or named in the request).
**Precedence: lockfile > manifest.** Check in this order per ecosystem:

| Ecosystem | Lockfiles (checked first, in order) | Manifest (fallback) |
|---|---|---|
| npm | `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lockb` / `bun.lock` | `package.json` |
| PyPI | `poetry.lock`, `uv.lock`, `Pipfile.lock`, `requirements*.txt` | `pyproject.toml` |
| crates | `Cargo.lock` | `Cargo.toml` |
| Go | `go.mod` (+ `go.sum`) | `go.mod` |

If more than one ecosystem is detected (e.g. a monorepo mixing npm and PyPI),
resolve relative to the file currently in focus; if genuinely ambiguous, ask
which package/workspace.

## 2. Resolve installed version

Read the concrete pinned version straight from the lockfile when one exists —
this is the **locked** version. If only a manifest range is available (no
lockfile, or the package isn't in the lockfile), resolve the range to the
concrete latest-satisfying version via the registry, and explicitly note that
this version is **inferred**, not locked, when citing it later. Never silently
treat an inferred version as if it were pinned.

## 3. Registry lookup

`WebFetch` the registry metadata for the package + version to confirm the
version exists and to obtain the repository URL / docs / homepage needed for
step 4:

- **npm:** `https://registry.npmjs.org/<pkg>` (and `https://registry.npmjs.org/<pkg>/<version>`)
- **PyPI:** `https://pypi.org/pypi/<pkg>/<version>/json`
- **crates:** `https://crates.io/api/v1/crates/<crate>`
- **Go:** `https://proxy.golang.org/<module>/@v/<version>.info`

## 4. Fetch version-pinned docs

Using the metadata from step 3, fetch the actual documentation for that exact
version, following the ecosystem's recipe (`references/ecosystem-<npm|pypi|crates|go>.md`
for the full template and worked examples). The doc-source precedence (verbatim
from the design's Global Constraints) is:

> Rust → `https://docs.rs/<crate>/<version>/<crate>/`. Go → `https://pkg.go.dev/<module>@<version>`. npm → GitHub docs at matching tag (`raw.githubusercontent.com/<owner>/<repo>/<tag>/…`), else `unpkg.com/<pkg>@<version>/README.md`. PyPI → Read the Docs versioned (`<proj>.readthedocs.io/en/<version>/`), else GitHub tag docs, else PyPI per-version description. Prefer `llms.txt`/`llms-full.txt` when the host publishes one.

Always fetch the **version-pinned** URL, never a "latest"/unversioned alias,
unless step 2 already labeled the version as inferred or one of the
Fallbacks below applies.

## 5. Distill + ground

Extract what's relevant to the question from the fetched docs, then write or
explain the code against it, citing the resolved version and the exact URL(s)
fetched. If a requested symbol isn't present in the resolved version's docs,
say so plainly instead of guessing. See `output-contract.md` for the full
citation format, and `caching.md` for writing the distilled result through to
the cache after a successful fetch.

## Fallbacks

When the version-pinned path in step 4 can't be satisfied, walk this chain and
label the result honestly rather than silently substituting:

These labels are the canonical strings docpin prints; see `output-contract.md`
for how they attach to the answer.

- **No lockfile / version unresolvable:** fall back to the latest published
  version and label the answer explicitly as *latest (unpinned)*.
- **Doc host 404 at that exact version:** walk the fallback chain in the
  ecosystem recipe; if only a nearby version has docs, use it and label the
  answer as *closest available (<v>)*.
- **Private/unpublished package:** registry lookup fails entirely → offer the
  locally installed copy's bundled docs if present (`node_modules/<pkg>/README*`,
  the package's site-packages `dist-info`, a vendored crate/module), clearly
  labeled as *local bundled*.

In every case, the honesty invariant from `SKILL.md` still applies: state the
version and source actually used, and never present a fallback result as if it
were the version-pinned exact match.
