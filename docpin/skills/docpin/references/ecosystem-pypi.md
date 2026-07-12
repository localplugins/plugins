# ecosystem-pypi.md — PyPI recipe

Ecosystem-specific fill-in for the `resolver.md` loop: lockfiles/manifest,
registry endpoint, doc-URL template, and fallback chain for PyPI packages.

## Lockfiles

Checked in this order (first match wins); precedence is lockfile > manifest:

1. `poetry.lock`
2. `uv.lock`
3. `Pipfile.lock`
4. `requirements*.txt` (e.g. `requirements.txt`, `requirements-dev.txt` — pins
   only when the file uses `==`; a range like `>=` is not a lock)
5. `pyproject.toml` (manifest fallback — only when no lockfile pins the
   package; resolved version is **inferred**, not locked)

## Registry

- `https://pypi.org/pypi/<pkg>/<version>/json` — full metadata for one exact
  version.

Relevant fields for step 4 of the resolver:

- `info.project_urls` — look for keys like `Documentation`, `Source`,
  `Repository`, `Homepage` (case varies by project); resolve a GitHub
  `<owner>/<repo>` from whichever points at GitHub.
- `info.home_page` — legacy single homepage field, used when
  `project_urls` is absent or doesn't include a usable link.

## Doc URL

Preferred order:

1. **Read the Docs, versioned:** `https://<project>.readthedocs.io/en/<version>/`.
   Read the Docs version slugs vary by project — try `v<version>` and
   `<version>` (e.g. `en/v0.111.0/` vs `en/0.111.0/`) and confirm which
   resolves rather than guessing blind.
2. **GitHub tag docs**, when Read the Docs isn't available or doesn't have a
   matching version slug: resolve `<owner>/<repo>` from `project_urls`/
   `home_page`, resolve the tag (`v<version>` or `<version>`), then fetch
   `https://raw.githubusercontent.com/<owner>/<repo>/<tag>/README.md` and
   `/docs/**`.
3. **PyPI per-version long description**, as a last resort: the `info.description`
   field of the `/pypi/<pkg>/<version>/json` response already fetched in the
   registry step — always available, always version-pinned, but usually
   thinner than dedicated docs.

Prefer a published `llms.txt`/`llms-full.txt` over any of the above when the
project publishes one (check the repo root and the Read the Docs site).

## Fallback

1. Read the Docs versioned (above) — primary path.
2. GitHub tag docs (above).
3. PyPi per-version description (above).
4. Latest published version's docs, explicitly labeled *latest (not pinned in
   this project)* — only when the pinned version has no reachable docs
   anywhere above.

## Worked example: `fastapi@0.111.0`

1. **Lockfile:** `poetry.lock` pins `fastapi` at `0.111.0`.
2. **Registry:** `GET https://pypi.org/pypi/fastapi/0.111.0/json` →
   `info.project_urls["Documentation"]` = `https://fastapi.tiangolo.com/`,
   `info.project_urls["Source"]` = `https://github.com/fastapi/fastapi`.
3. **Doc URL:** FastAPI's docs site isn't Read the Docs, so try the
   documented site first for a version match; if it isn't version-selectable,
   fall to GitHub tag docs: resolve tag `0.111.0` (FastAPI tags without the
   `v` prefix) →
   `https://raw.githubusercontent.com/fastapi/fastapi/0.111.0/README.md`
   and `docs/en/docs/**` for topic pages.
4. **Cite:** "fastapi@0.111.0 (locked), source:
   `https://raw.githubusercontent.com/fastapi/fastapi/0.111.0/docs/en/docs/index.md`"
   (or the specific topic page fetched).
