---
name: runner-detection
description: Use to figure out how to run a repo's tests and type/compile checks, and to write the green-keeper config. Covers common ecosystems and the config schema.
---

# Runner Detection

Green Keeper needs two concrete shell commands for a repo: how to run the tests, and how to run the type/compile check. Detect them, confirm with the user, and cache them to `.green-keeper/config.json`.

## Use when

- Running `/green-setup` on a new repo.
- A configured command is wrong and needs re-detecting.
- Writing or editing `.green-keeper/config.json`.

## Decision guide

1. **Identify the ecosystem** from the manifest present: `package.json` (Node/TS), `pyproject.toml`/`setup.cfg`/`tox.ini` (Python), `go.mod` (Go), `Cargo.toml` (Rust), `Makefile` (any).
2. **Read the real commands, don't guess them.** Prefer `scripts`/targets already defined; CI config (`.github/workflows`) usually names the exact commands the team runs.
3. **Pick a fast `quickTest`.** The hooks run it on every turn end and session start, so choose a changed-files or single-package subset when one exists; otherwise fall back to the full `test`.
4. **Honor explicit overrides** from `--test` / `--typecheck` / `--quick` arguments — they win over detection.
5. **Confirm before saving.** These commands run automatically via hooks. Show them and get a yes.
6. **Never guess a destructive command.** If you can't detect one, ask the user.

## Quick reference

| Ecosystem | Typical `test` | Typical `typecheck` |
| --- | --- | --- |
| Node / TS | `npm test` / `vitest run` / `jest` | `tsc --noEmit` |
| Python | `pytest` | `mypy .` or `pyright` |
| Go | `go test ./...` | `go build ./...` or `go vet ./...` |
| Rust | `cargo test` | `cargo check` |
| Make-based | `make test` | `make check` / `make lint` |

## Deep references

- **`references/ecosystem-detection.md`** — per-ecosystem detection walkthroughs (where to look, which runner to infer, how to pick a fast `quickTest`), plus Make/CI fallbacks.
- **`references/config-schema.md`** — the full `.green-keeper/config.json` schema: every field, type, default, validation notes, and worked examples per ecosystem.
