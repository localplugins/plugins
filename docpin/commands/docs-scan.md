---
description: Report which of this project's direct dependencies docpin can resolve version-matched documentation for.
---

# /docs-scan

A coverage report over this project's dependencies — no `$ARGUMENTS`. This
is lighter than `/docs`: it uses local manifest/lockfile parsing plus
registry metadata only, and never fetches or distills a full doc page.

1. **Detect ecosystems** — scan the project root (and one level of obvious
   subdirs for monorepos) for the lockfiles/manifests listed in
   `skills/docpin/references/resolver.md` §1 (npm, PyPI, crates, Go).
2. **Enumerate direct dependencies** — for each detected ecosystem, list its
   direct (top-level) dependencies and their pinned/resolved versions,
   using the same lockfile-over-manifest precedence as the skill.
3. **Classify resolvability** — for each dependency, determine whether
   docpin can reach a version-pinned doc source for it by checking the
   doc-source precedence in the ecosystem's recipe
   (`references/ecosystem-npm.md`, `ecosystem-pypi.md`,
   `ecosystem-crates.md`, `ecosystem-go.md`) — registry metadata lookup is
   enough for this; do not fetch/distill the full doc page. Classify each
   as:
   - `✓` — resolvable: the primary version-pinned doc source (or a
     documented fallback source) exists for the resolved version.
   - `fallback` — only reachable via a fallback in
     `references/resolver.md` §5 (e.g. only a closest-available version has
     docs, or only local bundled docs are available).
   - `✗` — unresolvable: no registry entry, no doc source, and no local
     bundled docs found.
4. **Print one line per dependency**, grouped by ecosystem:

   ```
   name  version  <✓ | fallback | ✗>
   ```

5. **Summarize coverage** at the end: total dependencies scanned per
   ecosystem and overall, and counts for each of `✓` / `fallback` / `✗`.

This command never writes files and never fetches full documentation — it's
a fast, read-mostly report suitable for a quick health check or a demo.
