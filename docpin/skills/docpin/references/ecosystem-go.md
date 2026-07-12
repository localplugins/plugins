# ecosystem-go.md — Go modules recipe

Ecosystem-specific fill-in for the `resolver.md` loop: lockfiles/manifest,
registry/proxy endpoint, doc-URL template, and fallback chain for Go modules.

## Lockfiles

Go has a single manifest+lock pair rather than a separate lockfile format:

1. `go.mod` — declares the module and its direct/indirect requirements with
   exact versions (Go's `require` directives are already pinned versions, not
   ranges, so `go.mod` functions as the lock here).
2. `go.sum` — cryptographic checksums confirming the resolved module graph;
   read alongside `go.mod` to confirm the exact version actually in use,
   never treated as a manifest fallback on its own.

There is no separate "manifest fallback" tier for Go the way npm/PyPI/crates
have lockfile-vs-manifest — a version present in `go.mod` is already
considered locked.

## Registry

Go's registry is the module proxy:

- `https://proxy.golang.org/<module>/@v/<version>.info` — confirms the
  version exists and returns its canonical version string + commit time.
  (`<module>` must be lowercase-escaped per the proxy protocol, e.g. uppercase
  letters become `!lowercase`.)

Use this to confirm the pinned version resolves before fetching docs; it does
not itself return a repository URL — the module path *is* the repository
location for the common case of GitHub-hosted modules
(`github.com/<owner>/<repo>[/<subpkg>...]`).

## Doc URL

pkg.go.dev is Go's native, exact-version doc host — no tag resolution or
GitHub round-trip needed for the primary path:

- `https://pkg.go.dev/<module>@<version>` — rendered package docs for that
  exact version.
- For a specific symbol, append a fragment: `https://pkg.go.dev/<module>@<version>#<Symbol>`.

**Module path vs. package path:** the module path (declared in `go.mod`'s
first line, e.g. `github.com/gin-gonic/gin`) is not always what you want to
browse directly — a module can contain multiple importable sub-packages. When
the code imports a sub-package, use the sub-package's import path in the URL,
not just the module root, e.g.
`https://pkg.go.dev/<module>@<version>/<subpkg>` (for example
`github.com/gin-gonic/gin@v1.9.1/binding`, a sub-package of the `gin` module).

## Fallback

1. `https://pkg.go.dev/<module>@<version>` (above) — primary path.
2. `https://pkg.go.dev/<module>` (latest), explicitly labeled *latest (not
   pinned in this project)* — only when pkg.go.dev has no page for the exact
   pinned version (rare; e.g. a very fresh tag pkg.go.dev hasn't indexed yet).
3. Repository README at the matching tag: the module path for a
   GitHub-hosted module already gives `<owner>/<repo>`; resolve the tag
   (Go modules are tagged `v<version>`, e.g. `v1.9.1`) →
   `https://raw.githubusercontent.com/<owner>/<repo>/<tag>/README.md` — used
   when pkg.go.dev is unreachable or the module is hosted privately/on a
   proxy that doesn't mirror to pkg.go.dev.

## Worked example: `github.com/gin-gonic/gin@v1.9.1`

1. **Lockfile:** `go.mod` requires `github.com/gin-gonic/gin v1.9.1`; `go.sum`
   has matching checksums.
2. **Registry:** `GET https://proxy.golang.org/github.com/gin-gonic/gin/@v/v1.9.1.info`
   confirms the version exists.
3. **Doc URL:** `https://pkg.go.dev/github.com/gin-gonic/gin@v1.9.1` — for the
   `Context.JSON` method, `https://pkg.go.dev/github.com/gin-gonic/gin@v1.9.1#Context.JSON`.
   If the code imports the `binding` sub-package specifically, use
   `https://pkg.go.dev/github.com/gin-gonic/gin@v1.9.1/binding` instead.
4. **Cite:** "github.com/gin-gonic/gin@v1.9.1 (locked), source:
   `https://pkg.go.dev/github.com/gin-gonic/gin@v1.9.1#Context.JSON`".
