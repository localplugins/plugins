# Changelog

All notable changes to the **localplugins** marketplace are documented here. This project follows [Semantic Versioning](https://semver.org).

## [0.4.0] — 2026-07-10

Added a fifth plugin.

### Added
- **brand-forge** — generate on-brand logos, social templates, and marketing
  graphics from a saved visual brand profile (palette, type, logo, tone). The
  vector (SVG) engine runs entirely on your machine — no accounts or keys; AI
  imagery is opt-in, off by default, and only reaches the network with your own
  provider key. The visual counterpart to content-multiplier (shares the same
  `brand/` folder). Commands: `/brand-new`, `/brand-make`, `/brand-status`,
  `/brand-use`, `/brand-export`.

## [0.3.0] — 2026-07-09

Added a fourth plugin and broadened the marketplace's framing.

### Added
- **docpin** — grounds Claude in documentation matched to the library versions installed in your project (npm, PyPI, crates.io, Go). It resolves each dependency's installed version from your lockfiles and fetches version-pinned docs on demand, always citing the version and source URL. Commands: `/docs`, `/docs-scan`, `/docs-setup`, plus a local-only SessionStart version-map hook.

### Changed
- Repositioned localplugins from "plugins where nothing leaves your machine" to **a local community of Claude Code plugins**. The three original plugins still run entirely on your machine and say so per-plugin; docpin fetches from public registries and doc hosts (always cited). The marketplace no longer makes a blanket no-network claim, since docpin uses the web by design.

## [0.2.1] — 2026-07-08

Documentation polish across all three plugins.

### Added
- A **Requirements** section to each plugin (what you need before installing).
- An **Uninstall** section to each plugin.

### Changed
- Standardized README headings to **Installation** and **Usage examples**.

## [0.2.0] — 2026-07-08

Documentation and depth pass across all three plugins.

### Added
- Comprehensive READMEs for every plugin — dedicated install guides, concrete usage walkthroughs, full command references, configuration docs, and troubleshooting.
- Enriched skills: each skill is now a navigation `SKILL.md` plus a `references/` folder with worked examples, detailed rules, and edge cases.
- Per-plugin diagrams and a marketplace banner.
- Repo-level `LICENSE`, `CONTRIBUTING.md`, and this changelog.

### Changed
- Trimmed repeated "runs locally" messaging down to a single clear statement per doc.

## [0.1.0] — 2026-07-07

Initial public release — three local-first Claude Code plugins.

### Added
- **content-multiplier** — turn one source (a post, transcript, or idea) into on-brand, multi-channel, multi-language content. Commands: `/brand-setup`, `/multiply`, `/campaign`, `/localize`, `/review`.
- **green-keeper** — keep your tests and types green while you code, with a no-fake-green guarantee and automatic Stop-hook enforcement. Commands: `/green`, `/cover`, `/green-setup`.
- **money-map** — understand any bank or card CSV locally: categorize transactions, summarize cash flow, and flag anomalies, with deterministic arithmetic. Commands: `/understand`, `/money-setup`, `/reconcile`, `/clean`, `/report`.

All three run locally — no accounts, no API keys, nothing leaves your machine.
