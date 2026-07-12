# Contributing

Thanks for your interest in **localplugins** — a small, community-built collection of Claude Code plugins.

## Report an issue or request a plugin
- Open an issue: <https://github.com/localplugins/plugins/issues>
- Or email: **localplugins@proton.me**

When reporting a bug, include your OS, the plugin and command, and (for money-map) a small sample of the CSV format that tripped it up.

## Repository layout
Each plugin lives in its own top-level directory:

```
<plugin>/
  .claude-plugin/plugin.json   # manifest: name, description, version, license, keywords
  commands/                    # slash commands
  agents/                      # subagents
  skills/                      # skills (SKILL.md + references/)
  hooks/                       # lifecycle hooks (where used)
```

The marketplace manifest is `.claude-plugin/marketplace.json`.

## Validate before opening a PR
Structural validation runs on pure Python standard library (no dependencies):

```bash
python3 tests/validate.py            # run all checks
python3 tests/test_moneymap.py       # money-map unit tests
```

## Principles
- **Honest about I/O:** state each plugin's network posture plainly. Most localplugins run entirely on your machine — no accounts, no API keys, no network, no telemetry, reading only the files they're pointed at. A plugin that does reach the network (like docpin, which fetches version-matched docs) must say so and cite what it fetches — never claim "nothing leaves your machine" when it isn't true.
- **No fabrication:** where a plugin produces numbers (e.g. money-map), the math is real code and traces to the source data — never model-guessed.
- **Plain voice:** clear, confident, no hype.

## License
By contributing, you agree your contributions are licensed under the [MIT License](LICENSE).
