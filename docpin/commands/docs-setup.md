---
description: Detect ecosystems in this project and write or update the docpin config at .docpin/config.json.
---

# /docs-setup

One-time (or re-runnable) setup — no `$ARGUMENTS`. Detects this project's
ecosystems and writes the docpin config file.

1. **Detect ecosystems** — scan for the lockfiles/manifests listed in
   `skills/docpin/references/resolver.md` §1 (npm, PyPI, crates, Go) and
   report which were found.
2. **Create or update `.docpin/config.json`** with this exact default
   schema (per the design spec §8) if the file doesn't already exist; if it
   already exists, preserve the user's existing values and only fill in any
   fields that are missing:

   ```json
   {
     "cache": { "enabled": true, "dir": ".docpin/cache" },
     "hook": { "enabled": true, "maxDeps": 40 },
     "defaultEcosystem": null
   }
   ```

3. **Explain each field** to the user:
   - `cache.enabled` — default `true`; when `false`, docpin skips the
     on-disk cache entirely and always fetches fresh (see
     `skills/docpin/references/caching.md`).
   - `cache.dir` — default `.docpin/cache`; where cached, distilled doc
     entries are written, keyed `<ecosystem>/<pkg>@<version>[/topic]`.
   - `hook.enabled` — default `true`; controls whether the SessionStart
     hook (`hooks/session-start.sh`) injects a version map at session
     start. Set `false` to disable it.
   - `hook.maxDeps` — default `40`; the maximum number of dependencies the
     SessionStart hook lists per ecosystem before truncating (it always
     notes when truncation happened).
   - `defaultEcosystem` — default `null`; set to one of `"npm"`, `"pypi"`,
     `"crates"`, or `"go"` to resolve ambiguity when a bare library name
     exists in more than one ecosystem detected in this project.
   - If the user asks to change a value now (e.g. disable the hook, change
     `maxDeps`, or set a `defaultEcosystem`), update the corresponding
     field(s) in `.docpin/config.json` accordingly.
4. **Confirm `.docpin/` is git-ignored** — check the project's
   `.gitignore` for a `.docpin/` (or equivalent) entry; if missing, append
   one. `.docpin/config.json` and `.docpin/cache/` are project-local
   derived/config state and should never be committed.

Defaults apply even without running this command — `/docs-setup` just makes
the config explicit and gives the user a place to change it.
