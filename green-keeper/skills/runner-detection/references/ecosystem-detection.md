# Per-ecosystem runner detection

Goal: for the repo at hand, produce a concrete `test` command, a concrete `typecheck` command, and (when possible) a fast `quickTest` subset. Read the project's real configuration rather than assuming — CI config in particular usually names the exact commands the team relies on.

Always confirm the detected commands with the user before saving. They run automatically via the hooks.

---

## Node / TypeScript

**Where to look**

- `package.json` → `scripts`. A `test` script is your `test`; a `typecheck` or `check-types` script is your `typecheck`.
- `tsconfig.json` present but no typecheck script → `tsc --noEmit`.
- `devDependencies` reveals the runner: `vitest`, `jest`, `mocha`, `ava`.
- The package manager: `pnpm-lock.yaml` → `pnpm`, `yarn.lock` → `yarn`, `bun.lockb` → `bun`, else `npm`. Use the matching runner (`pnpm test`, `yarn test`, etc.).
- Monorepos: `pnpm -r test` / `turbo run test` / `nx run-many` may be the real entry point — check `turbo.json`, `nx.json`, or workspace globs.

**Typical results**

- `test`: `npm test` / `pnpm test` / `vitest run` / `jest`
- `typecheck`: `tsc --noEmit` (or `tsc -p tsconfig.json --noEmit`)
- `quickTest`: `vitest run --changed` (Vitest), `jest --onlyChanged` (Jest, git-aware), or `vitest run path/to/dir`.

**Notes**

- Prefer non-watch, non-interactive forms: `vitest run` not `vitest`, so the command exits.
- If tests need a build first, the `test` script usually chains it; don't invent a separate build step.

---

## Python

**Where to look**

- `pyproject.toml` → `[tool.pytest.ini_options]`, `[tool.poetry]`, or a `[project.scripts]`/`tox` setup. `setup.cfg` `[tool:pytest]`, or `tox.ini`.
- `pytest` present/configured → `test` is `pytest`.
- Type check: `mypy` if `[tool.mypy]` or `mypy.ini` exists → `mypy .` (or the configured package path). `pyright`/`pyrightconfig.json` → `pyright`.
- Runner wrapper: Poetry → `poetry run pytest` / `poetry run mypy .`; Hatch, PDM, or a virtualenv may prefix commands. Match what the project uses.

**Typical results**

- `test`: `pytest` (or `poetry run pytest`)
- `typecheck`: `mypy .` or `pyright`
- `quickTest`: `pytest -q -k <affected>`, `pytest <path/to/test_file.py>`, or `pytest --lf` (last-failed).

**Notes**

- If there's no type checker configured at all, ask the user rather than forcing one on the repo. A `typecheck` that no one runs will just be noise.

---

## Go

**Where to look**

- `go.mod` marks a Go module.
- Tests: `go test ./...` runs the whole module.
- Type/compile check: `go build ./...` (compiles everything) or `go vet ./...` (compile + common-mistake analysis). `go vet` is the stricter, more useful check.

**Typical results**

- `test`: `go test ./...`
- `typecheck`: `go vet ./...` (or `go build ./...`)
- `quickTest`: `go test ./path/to/pkg/...` for the package(s) you're touching.

**Notes**

- For large modules, a full `go test ./...` can be slow — scope `quickTest` to the affected package.

---

## Rust

**Where to look**

- `Cargo.toml` marks a crate/workspace.
- Tests: `cargo test`.
- Type/compile check: `cargo check` (fast, no codegen). Add `cargo clippy` only if the repo already uses it.
- Workspaces: `cargo test --workspace` and `cargo check --workspace`.

**Typical results**

- `test`: `cargo test`
- `typecheck`: `cargo check`
- `quickTest`: `cargo test -p <crate>` or `cargo test <name-filter>`.

---

## Make-based and other projects

**Where to look**

- `Makefile` with `test`, `check`, `lint`, or `typecheck` targets → `make test`, `make check`, etc. These are often the canonical entry points; use them over raw tool invocations.
- `Justfile` (`just test`), `Taskfile.yml` (`task test`), or a `scripts/` directory.
- **CI config is the source of truth.** `.github/workflows/*.yml`, `.gitlab-ci.yml`, `.circleci/config.yml`, or `Jenkinsfile` list the exact commands that gate merges. When a repo's local tooling is unclear, read CI and mirror it.

---

## Choosing `quickTest`

The hooks run `quickTest` (falling back to `test`) on every session start and turn end, so speed matters.

Prefer, in order:

1. **Changed-files subset** — `vitest run --changed`, `jest --onlyChanged`, `pytest --lf` / `-k <affected>`.
2. **Single package/dir** — `go test ./pkg/...`, `cargo test -p crate`, `pytest tests/unit`.
3. **Full test** — fall back to the full `test` command only if no fast subset exists.

If the full suite is fast enough (a few seconds), it's fine to set `quickTest` equal to `test`.

## When detection fails

If you cannot confidently detect a command:

- Ask the user for it directly.
- Never guess a command that could be destructive (anything that writes, deploys, migrates, or deletes). A test/typecheck command should only read and compile/run tests.
