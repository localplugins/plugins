# ecosystem-crates.md — crates.io (Rust) recipe

Ecosystem-specific fill-in for the `resolver.md` loop: lockfiles/manifest,
registry endpoint, doc-URL template, and fallback chain for Rust crates.

## Lockfiles

Checked in this order (first match wins); precedence is lockfile > manifest:

1. `Cargo.lock`
2. `Cargo.toml` (manifest fallback — only when no `Cargo.lock` is present, or
   the crate isn't pinned in it; resolved version is **inferred**, not
   locked)

## Registry

- `https://crates.io/api/v1/crates/<crate>` — full metadata (all versions,
  repository/homepage links).
- `https://crates.io/api/v1/crates/<crate>/<version>` — metadata for one
  exact version.

Relevant fields for step 4 of the resolver: `crate.repository` (GitHub/GitLab
source URL) and `crate.homepage`, used only as a fallback — docs.rs (below)
is the primary, native doc source and needs no repo resolution at all.

## Doc URL

crates.io's ecosystem has a native, exact-version doc host, so no tag
resolution or GitHub round-trip is needed for the primary path:

- `https://docs.rs/<crate>/<version>/<crate>/` — the crate's rustdoc output
  built for that exact published version. Most reliable source in this
  recipe.
- For a specific topic/item, append the item path, e.g.
  `https://docs.rs/<crate>/<version>/<crate>/struct.SomeType.html`, or use
  the docs.rs search box equivalent, `?search=<query>`, against the base
  crate URL.

## Fallback

1. `https://docs.rs/<crate>/<version>/<crate>/` (above) — primary path;
   docs.rs builds docs for essentially every published version, so this
   should resolve in the overwhelming majority of cases.
2. `https://docs.rs/<crate>/latest/<crate>/`, explicitly labeled *latest (not
   pinned in this project)* — only when docs.rs has no build for the exact
   pinned version (e.g. a build failure on that version).
3. Repository README at the matching tag (resolve `crate.repository` →
   `<owner>/<repo>`, tag `v<version>` or `<version>`) →
   `https://raw.githubusercontent.com/<owner>/<repo>/<tag>/README.md` — used
   when docs.rs has nothing at all for the crate (rare; e.g. yanked or
   docs-disabled crates).

## Worked example: `serde@1.0.196`

1. **Lockfile:** `Cargo.lock` pins `serde` at `1.0.196`.
2. **Registry:** `GET https://crates.io/api/v1/crates/serde/1.0.196` confirms
   the version exists and is not yanked.
3. **Doc URL:** `https://docs.rs/serde/1.0.196/serde/` — for a specific
   question (e.g. the `Deserializer` trait),
   `https://docs.rs/serde/1.0.196/serde/trait.Deserializer.html`.
4. **Cite:** "serde@1.0.196 (locked), source:
   `https://docs.rs/serde/1.0.196/serde/trait.Deserializer.html`".
