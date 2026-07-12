#!/usr/bin/env python3
"""Behavioral tests for green-keeper's Stop hook decision logic. Pure stdlib."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOK = ROOT / "green-keeper" / "hooks" / "check-green.sh"
FAILS = []


def run_stop(tmp, cfg, baseline="green", attempts="0"):
    gk = Path(tmp) / ".green-keeper"
    (gk / "state").mkdir(parents=True, exist_ok=True)
    (gk / "config.json").write_text(json.dumps(cfg))
    (gk / "state" / "baseline").write_text(baseline)
    (gk / "state" / "attempts").write_text(attempts)
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp)}
    p = subprocess.run([str(HOOK)], input=json.dumps({"hook_event_name": "Stop", "cwd": str(tmp)}),
                       capture_output=True, text=True, env=env)
    return p.returncode, p.stdout.strip()


def check(cond, name):
    print(f"{'PASS' if cond else 'FAIL'}: {name}")
    if not cond:
        FAILS.append(name)


def main():
    green = {"test": "true", "typecheck": "true", "quickTest": "true", "enforce": True, "maxAttempts": 3}
    red = {"test": "false", "typecheck": "true", "quickTest": "false", "enforce": True, "maxAttempts": 3}
    with tempfile.TemporaryDirectory() as t:
        rc, out = run_stop(t, green, baseline="green")
        check(rc == 0 and out == "", "green -> allow stop, no block")

        rc, out = run_stop(t, red, baseline="green", attempts="0")
        blocked = bool(out) and json.loads(out).get("decision") == "block"
        check(rc == 0 and blocked, "new red + baseline green -> block")

        rc, out = run_stop(t, red, baseline="red", attempts="0")
        check(rc == 0 and out == "", "pre-existing red (baseline red) -> allow stop")

        rc, out = run_stop(t, {**red, "enforce": False}, baseline="green")
        check(rc == 0 and out == "", "enforce false -> allow stop")

        rc, out = run_stop(t, red, baseline="green", attempts="3")
        check(rc == 0 and out == "", "attempts at max -> yield (allow stop)")
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
