# The `.green-keeper/config.json` schema

Green Keeper reads one config file at the repo root: `.green-keeper/config.json`. `/green-setup` writes it; you can also edit it by hand. Commit this file so the whole team (and the hooks) share the same commands.

## Fields

| Field | Type | Required | Default | Meaning |
| --- | --- | --- | --- | --- |
| `test` | string | yes | — | Full test command. Run by `/green` and `/cover`. |
| `typecheck` | string | yes | — | Type/compile check command. Run by `/green`, both hooks, and the opt-in PostToolUse check. |
| `quickTest` | string | no | falls back to `test` | Fast subset the hooks run on every session start and turn end. Keep it quick. |
| `enforce` | boolean | no | `true` | When `true`, the Stop hook blocks a turn from ending on newly-introduced red. `false` makes the Stop hook report-only. |
| `maxAttempts` | number | no | `3` | How many times the Stop hook re-blocks to push a fix before yielding and leaving the red for the human. |
| `postToolUseTypecheck` | boolean | no | `false` | Opt-in. After each `Write`/`Edit`/`MultiEdit`, run the typecheck and surface new type errors as a note. Report-only; never blocks. |

## How the hooks read the fields

- **SessionStart** runs `typecheck` and `quickTest` (or `test` if `quickTest` is absent) by exit code, records a `green`/`red` baseline in `.green-keeper/state/baseline`, and resets the attempt counter. No config → it prompts you to run `/green-setup` and does nothing else.
- **Stop** runs `typecheck` and `quickTest`. It blocks only when there is red **and** `enforce` is `true` **and** the baseline was `green` (the red is new this session). It re-blocks up to `maxAttempts`, then yields.
- **PostToolUse** runs only if `postToolUseTypecheck` is `true`, runs `typecheck`, and reports new type errors. It cannot block.

Because `quickTest` runs on every turn end, an expensive `quickTest` slows the whole session. Scope it (see `ecosystem-detection.md`).

## Validation notes

- `test` and `typecheck` are required. If either is missing, detection is incomplete — ask the user.
- Commands are executed via the shell (`eval` inside the hook), so they may include flags, pipes, and `&&` chains, but keep them non-interactive and non-watch so they exit on their own.
- Never write a destructive command here. These strings run automatically at session start and turn end — treat editing them with the same trust as editing `package.json` scripts or a `Makefile`.
- Booleans are real JSON booleans (`true`/`false`), not strings. `maxAttempts` is a number.

## State directory (not part of config)

Alongside the config, Green Keeper keeps `.green-keeper/state/`:

- `baseline` — `green` or `red`, recorded at session start.
- `attempts` — the Stop hook's per-session counter.

Add `.green-keeper/state/` to `.gitignore`. It's per-machine and must not be shared. The `config.json` itself is safe (and meant) to commit.

## Worked examples

### TypeScript with Vitest

```json
{
  "test": "npm test",
  "typecheck": "tsc --noEmit",
  "quickTest": "vitest run --changed",
  "enforce": true,
  "maxAttempts": 3,
  "postToolUseTypecheck": false
}
```

### Python with pytest + mypy, edit-time feedback on

```json
{
  "test": "pytest",
  "typecheck": "mypy .",
  "quickTest": "pytest -q -k affected",
  "enforce": true,
  "maxAttempts": 2,
  "postToolUseTypecheck": true
}
```

### Go module

```json
{
  "test": "go test ./...",
  "typecheck": "go vet ./...",
  "quickTest": "go test ./internal/...",
  "enforce": true,
  "maxAttempts": 3,
  "postToolUseTypecheck": false
}
```

### Rust workspace

```json
{
  "test": "cargo test --workspace",
  "typecheck": "cargo check --workspace",
  "quickTest": "cargo test -p core",
  "enforce": true,
  "maxAttempts": 3,
  "postToolUseTypecheck": false
}
```

### Enforcement off (report-only)

```json
{
  "test": "make test",
  "typecheck": "make check",
  "enforce": false
}
```

With `enforce: false`, the Stop hook still runs the checks and prints the result to stderr but never blocks the turn. `quickTest` is omitted, so the hooks fall back to `test`.
