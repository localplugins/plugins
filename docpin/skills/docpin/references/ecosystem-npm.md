# ecosystem-npm.md — npm recipe

Ecosystem-specific fill-in for the `resolver.md` loop: lockfiles/manifest,
registry endpoint, doc-URL template, and fallback chain for npm packages.

## Lockfiles

Checked in this order (first match wins); precedence is lockfile > manifest:

1. `package-lock.json`
2. `pnpm-lock.yaml`
3. `yarn.lock`
4. `bun.lockb` / `bun.lock`
5. `package.json` (manifest fallback — only when no lockfile is present or the
   package isn't pinned in it; resolved version is **inferred**, not locked)

## Registry

- `https://registry.npmjs.org/<pkg>` — full metadata document (all versions,
  `dist-tags`, etc.)
- `https://registry.npmjs.org/<pkg>/<version>` — metadata for one exact
  version.

Relevant fields for step 4 of the resolver:

- `repository.url` — resolve to `<owner>/<repo>` on GitHub (strip
  `git+`/`git://`/`.git` and the `github:` shorthand).
- `homepage` — used when the repo doesn't resolve to GitHub, or as a secondary
  fallback source.

## Doc URL

Resolve `<owner>/<repo>` from `repository.url`, then resolve the tag: try
`v<version>` first, then `<version>` (both are common tagging conventions —
confirm against the repo's actual tags/releases rather than guessing blind).
With `<owner>/<repo>` and `<tag>` in hand:

- `https://raw.githubusercontent.com/<owner>/<repo>/<tag>/README.md`
- `https://raw.githubusercontent.com/<owner>/<repo>/<tag>/docs/**` (for
  deeper topic docs beyond the README)

Prefer a published `llms.txt` (e.g.
`https://raw.githubusercontent.com/<owner>/<repo>/<tag>/llms.txt` or a
project-hosted `llms.txt`/`llms-full.txt`) over the README when the project
publishes one — it's denser and model-oriented.

## Fallback

Walk this chain, in order, when the version-pinned GitHub tag docs above
aren't reachable:

1. GitHub tag docs (above) — primary path.
2. `https://unpkg.com/<pkg>@<version>/README.md` — same npm-published
   artifact, still version-pinned, useful when the GitHub repo/tag doesn't
   resolve.
3. The package's own versioned docs site, if `homepage` points to one with a
   version selector (e.g. `/docs/v<version>/...`).
4. Latest published version's docs, explicitly labeled *latest (not pinned in
   this project)* — only when none of the above resolve for the pinned
   version.

## Worked example: `react@18.2.0`

1. **Lockfile:** `package-lock.json` pins `react` at `18.2.0`.
2. **Registry:** `GET https://registry.npmjs.org/react/18.2.0` →
   `repository.url` = `git+https://github.com/facebook/react.git`, so
   `<owner>/<repo>` = `facebook/react`.
3. **Tag resolution:** React tags releases as `v18.2.0`.
4. **Doc URL:** `https://raw.githubusercontent.com/facebook/react/v18.2.0/README.md`
   (React's deeper docs live on a separate versioned site rather than
   `/docs/**` in-repo, so also check `homepage` —
   `https://react.dev` — for a version-matched section if the topic needs
   more than the README covers).
5. **Cite:** "react@18.2.0 (locked), source:
   `https://raw.githubusercontent.com/facebook/react/v18.2.0/README.md`".
