# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] — 2026-07-09

### Added

- `doc-fetcher` agent — runs the resolve → fetch → distill loop for one
  library in an isolated context, so a heavy multi-hop lookup doesn't spend
  the main session's context on raw registry JSON and fetched pages.
- `citation-guardian` agent — verifies a grounded answer's citations before
  it's trusted: re-resolves the cited version against the lockfile, confirms
  the cited URL resolves and is the version-pinned form, confirms cited
  symbols genuinely appear in that version's docs, and checks that any
  fallback is labeled honestly rather than passed off as an exact match.
- Substantially expanded `README.md`: per-ecosystem resolution notes and
  gotchas (npm monorepo/workspaces and scoped packages; PyPI manifest
  shapes, extras, and markers; crates.io sub-tables; Go module vs.
  sub-package paths and `v`-prefixed tags), more worked usage examples
  across npm/PyPI/crates.io, a commands table, an Agents & skills section,
  and an FAQ/troubleshooting section.
- `skills/docpin/SKILL.md` now notes when to delegate a fetch to
  `doc-fetcher` and when to verify an answer with `citation-guardian`.

## [0.1.0] — 2026-07-08

### Added

- Initial release: version-matched documentation grounding across npm,
  PyPI, crates.io, and Go modules.
- `docpin` skill — model-invoked; triggers before Claude writes or explains
  code that imports a third-party library, and runs the resolve → fetch →
  ground loop (detect ecosystem → resolve installed version → registry
  lookup → fetch version-pinned docs → distill and cite).
- `/docs <library> [topic]` — explicit pull of version-matched docs for a
  named library, optionally narrowed to a topic.
- `/docs-scan` — a coverage report of the project's direct dependencies and
  whether docpin can resolve version-pinned docs for each.
- `/docs-setup` — one-time configuration: detects ecosystems and writes
  `.docpin/config.json` (cache, hook, and default-ecosystem settings).
- Local-only SessionStart hook (`hooks/session-start.sh`) — reads
  lockfiles/manifests and injects a compact version-map context block at
  session start. Reads lockfiles only, makes no network access, and can be
  disabled.
- Project-local, opt-out doc cache keyed by `<ecosystem>/<pkg>@<version>[/topic]`.
- Zero-config by default: no API key, no account, no runtime dependency.
