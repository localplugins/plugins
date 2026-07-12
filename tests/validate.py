#!/usr/bin/env python3
"""Structural validator for the marketplace plugins (content-multiplier + green-keeper + money-map + docpin + brand-forge). Pure Python stdlib."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "content-multiplier"
GK = ROOT / "green-keeper"
MM = ROOT / "money-map"
DP = ROOT / "docpin"
BF = ROOT / "brand-forge"

CHECKS = {}
FAILURES = []


def register(name):
    def deco(fn):
        CHECKS[name] = fn
        return fn
    return deco


def ok(name):
    print(f"PASS: {name}")


def fail(name, msg):
    print(f"FAIL: {name}: {msg}")
    FAILURES.append(name)


def load_json(path):
    p = Path(path)
    if not p.exists():
        return None, f"missing file {p}"
    try:
        return json.loads(p.read_text()), None
    except json.JSONDecodeError as e:
        return None, f"invalid JSON in {p}: {e}"


def frontmatter(path):
    """Return (frontmatter_dict, body) or (None, reason) if absent/malformed."""
    p = Path(path)
    if not p.exists():
        return None, f"missing file {p}"
    text = p.read_text()
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
    if not m:
        return None, f"no frontmatter in {p}"
    fm = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fm[k.strip()] = v.strip().strip('"').strip("'")
    return fm, m.group(2)


def has_headings(path, headings):
    """Return list of missing '## ' headings (or a reason string if file absent)."""
    p = Path(path)
    if not p.exists():
        return f"missing file {p}"
    text = p.read_text()
    return [h for h in headings if f"# {h}" not in text]


@register("manifests")
def _manifests():
    mkt, err = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    if err:
        return fail("manifests", err)
    plug, err = load_json(PLUGIN / ".claude-plugin" / "plugin.json")
    if err:
        return fail("manifests", err)
    for field in ("name", "description", "version"):
        if field not in plug:
            return fail("manifests", f"plugin.json missing '{field}'")
    if plug["name"] != "content-multiplier":
        return fail("manifests", "plugin.json name must be 'content-multiplier'")
    names = [p.get("name") for p in mkt.get("plugins", [])]
    if "content-multiplier" not in names:
        return fail("manifests", "marketplace.json does not list content-multiplier")
    for p in mkt["plugins"]:
        if p.get("name") == "content-multiplier" and p.get("source") != "./content-multiplier":
            return fail("manifests", "content-multiplier source must be './content-multiplier'")
    ok("manifests")


BRAND_HEADINGS = {
    "brand-voice.md": ["Personality", "Tone", "Voice Do's", "Voice Don'ts",
                       "Signature Phrases", "Words to Avoid"],
    "messaging.md": ["Positioning", "Value Propositions", "Target Personas",
                     "Key Messages", "Boilerplate"],
    "style-guide.md": ["Formatting Rules", "Terminology & Glossary",
                       "Product & Trademark Names", "Banned Words", "Inclusive Language"],
    "compliance.md": ["Approved Claims", "Prohibited Terms", "Required Disclaimers",
                      "Regulated Language"],
}


@register("templates")
def _templates():
    base = PLUGIN / "templates" / "brand"
    for fname, headings in BRAND_HEADINGS.items():
        missing = has_headings(base / fname, headings)
        if isinstance(missing, str):
            return fail("templates", missing)
        if missing:
            return fail("templates", f"{fname} missing headings: {missing}")
    ok("templates")


@register("brand_setup")
def _brand_setup():
    fm, body = frontmatter(PLUGIN / "commands" / "brand-setup.md")
    if fm is None:
        return fail("brand_setup", body)
    if "description" not in fm:
        return fail("brand_setup", "brand-setup.md frontmatter missing 'description'")
    for token in ("content/brand", "Interview", "examples"):
        if token not in body:
            return fail("brand_setup", f"brand-setup body missing reference to '{token}'")
    ok("brand_setup")


@register("skill_brand_voice")
def _skill_brand_voice():
    fm, body = frontmatter(PLUGIN / "skills" / "brand-voice" / "SKILL.md")
    if fm is None:
        return fail("skill_brand_voice", body)
    for f in ("name", "description"):
        if f not in fm:
            return fail("skill_brand_voice", f"frontmatter missing '{f}'")
    if fm.get("name") != "brand-voice":
        return fail("skill_brand_voice", "name must be 'brand-voice'")
    for token in ("brand-voice.md", "messaging.md", "style-guide.md", "compliance.md"):
        if token not in body:
            return fail("skill_brand_voice", f"body must reference {token}")
    ok("skill_brand_voice")


CHANNELS = ["linkedin", "x-thread", "newsletter", "instagram", "youtube", "short-video", "blog"]


@register("skill_channels")
def _skill_channels():
    fm, body = frontmatter(PLUGIN / "skills" / "channel-formats" / "SKILL.md")
    if fm is None:
        return fail("skill_channels", body)
    if fm.get("name") != "channel-formats":
        return fail("skill_channels", "name must be 'channel-formats'")
    cdir = PLUGIN / "skills" / "channel-formats" / "channels"
    for ch in CHANNELS:
        f = cdir / f"{ch}.md"
        if not f.exists():
            return fail("skill_channels", f"missing channel spec {f}")
        for h in ("Format", "Length", "Structure", "Do", "Avoid"):
            if f"# {h}" not in f.read_text() and f"#{h}" not in f.read_text():
                return fail("skill_channels", f"{ch}.md missing '{h}' section")
        if ch not in body:
            return fail("skill_channels", f"SKILL.md must list channel '{ch}'")
    ok("skill_channels")


@register("skill_transcreation")
def _skill_transcreation():
    fm, body = frontmatter(PLUGIN / "skills" / "transcreation" / "SKILL.md")
    if fm is None:
        return fail("skill_transcreation", body)
    if fm.get("name") != "transcreation":
        return fail("skill_transcreation", "name must be 'transcreation'")
    for token in ("do-not-translate", "back-translation", "locales/"):
        if token not in body:
            return fail("skill_transcreation", f"body must reference '{token}'")
    ok("skill_transcreation")


def _check_agent(name, required_tokens):
    fm, body = frontmatter(PLUGIN / "agents" / f"{name}.md")
    if fm is None:
        return fail(f"agent_{name.replace('-', '_')}", body)
    for f in ("name", "description"):
        if f not in fm:
            return fail(f"agent_{name.replace('-', '_')}", f"frontmatter missing '{f}'")
    # zero-permission: if tools are declared, none may be network tools
    tools = fm.get("tools", "")
    for banned in ("WebFetch", "WebSearch"):
        if banned in tools:
            return fail(f"agent_{name.replace('-', '_')}", f"must not use {banned} (zero-permission)")
    for t in required_tokens:
        if t not in body:
            return fail(f"agent_{name.replace('-', '_')}", f"body must reference '{t}'")
    ok(f"agent_{name.replace('-', '_')}")


@register("agent_strategist")
def _agent_strategist():
    _check_agent("strategist", ["derivative plan", "persona"])


@register("agent_brand_guardian")
def _agent_brand_guardian():
    _check_agent("brand-guardian", ["compliance.md", "scorecard", "Prohibited Terms"])


@register("cmd_multiply")
def _cmd_multiply():
    fm, body = frontmatter(PLUGIN / "commands" / "multiply.md")
    if fm is None:
        return fail("cmd_multiply", body)
    if "description" not in fm:
        return fail("cmd_multiply", "frontmatter missing 'description'")
    for token in ("strategist", "brand-guardian", "channel-formats",
                  "content/output/", "index.md", "confirm", "--locales"):
        # case-insensitive: multiply.md uses "Confirm" (sentence-initial) vs. the "confirm" token
        if token.lower() not in body.lower():
            return fail("cmd_multiply", f"body must reference '{token}'")
    ok("cmd_multiply")


@register("cmd_localize")
def _cmd_localize():
    fm, body = frontmatter(PLUGIN / "commands" / "localize.md")
    if fm is None:
        return fail("cmd_localize", body)
    if "description" not in fm:
        return fail("cmd_localize", "frontmatter missing 'description'")
    for token in ("transcreation", "back-translation", "brand-guardian", "content/output/"):
        if token not in body:
            return fail("cmd_localize", f"body must reference '{token}'")
    ok("cmd_localize")


@register("cmd_review")
def _cmd_review():
    fm, body = frontmatter(PLUGIN / "commands" / "review.md")
    if fm is None:
        return fail("cmd_review", body)
    if "description" not in fm:
        return fail("cmd_review", "frontmatter missing 'description'")
    for token in ("brand-guardian", "scorecard", "redline"):
        if token not in body:
            return fail("cmd_review", f"body must reference '{token}'")
    ok("cmd_review")


@register("cmd_campaign")
def _cmd_campaign():
    fm, body = frontmatter(PLUGIN / "commands" / "campaign.md")
    if fm is None:
        return fail("cmd_campaign", body)
    if "description" not in fm:
        return fail("cmd_campaign", "frontmatter missing 'description'")
    for token in ("strategist", "calendar", "index.md", "content/output/", "brand-guardian"):
        if token not in body:
            return fail("cmd_campaign", f"body must reference '{token}'")
    ok("cmd_campaign")


@register("hooks")
def _hooks():
    hj, err = load_json(PLUGIN / "hooks" / "hooks.json")
    if err:
        return fail("hooks", err)
    if "SessionStart" not in hj.get("hooks", {}):
        return fail("hooks", "hooks.json missing SessionStart")
    script = PLUGIN / "hooks" / "session-start.sh"
    if not script.exists():
        return fail("hooks", "missing session-start.sh")
    text = script.read_text()
    for banned in ("curl", "wget", "nc "):
        if banned in text:
            return fail("hooks", f"session-start.sh must not use network tool '{banned.strip()}'")
    ok("hooks")


@register("readmes")
def _readmes():
    for path, must in [
        (ROOT / "README.md", ["content-multiplier", "/plugin marketplace add"]),
        (PLUGIN / "README.md", ["no accounts", "/brand-setup", "/multiply"]),
    ]:
        if not path.exists():
            return fail("readmes", f"missing {path}")
        text = path.read_text()
        for token in must:
            if token not in text:
                return fail("readmes", f"{path.name} must mention '{token}'")
    ok("readmes")


@register("gk_manifest")
def _gk_manifest():
    mkt, err = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    if err:
        return fail("gk_manifest", err)
    plug, err = load_json(GK / ".claude-plugin" / "plugin.json")
    if err:
        return fail("gk_manifest", err)
    if plug.get("name") != "green-keeper":
        return fail("gk_manifest", "plugin.json name must be 'green-keeper'")
    for field in ("description", "version"):
        if field not in plug:
            return fail("gk_manifest", f"plugin.json missing '{field}'")
    entry = next((p for p in mkt.get("plugins", []) if p.get("name") == "green-keeper"), None)
    if entry is None:
        return fail("gk_manifest", "marketplace.json does not list green-keeper")
    if entry.get("source") != "./green-keeper":
        return fail("gk_manifest", "green-keeper source must be './green-keeper'")
    ok("gk_manifest")


@register("gk_skill_anti_fake_green")
def _gk_skill_anti_fake_green():
    fm, body = frontmatter(GK / "skills" / "anti-fake-green" / "SKILL.md")
    if fm is None:
        return fail("gk_skill_anti_fake_green", body)
    if fm.get("name") != "anti-fake-green":
        return fail("gk_skill_anti_fake_green", "name must be 'anti-fake-green'")
    for token in ("skip", "revert", "@ts-ignore", "coverage"):
        if token not in body:
            return fail("gk_skill_anti_fake_green", f"body must reference '{token}'")
    ok("gk_skill_anti_fake_green")


@register("gk_skill_test_quality")
def _gk_skill_test_quality():
    fm, body = frontmatter(GK / "skills" / "test-quality" / "SKILL.md")
    if fm is None:
        return fail("gk_skill_test_quality", body)
    if fm.get("name") != "test-quality":
        return fail("gk_skill_test_quality", "name must be 'test-quality'")
    for token in ("behavior", "edge", "mock"):
        if token not in body:
            return fail("gk_skill_test_quality", f"body must reference '{token}'")
    ok("gk_skill_test_quality")


@register("gk_skill_runner_detection")
def _gk_skill_runner_detection():
    fm, body = frontmatter(GK / "skills" / "runner-detection" / "SKILL.md")
    if fm is None:
        return fail("gk_skill_runner_detection", body)
    if fm.get("name") != "runner-detection":
        return fail("gk_skill_runner_detection", "name must be 'runner-detection'")
    for token in (".green-keeper/config.json", "typecheck", "quickTest", "package.json", "pyproject.toml"):
        if token not in body:
            return fail("gk_skill_runner_detection", f"body must reference '{token}'")
    ok("gk_skill_runner_detection")


def _gk_agent(name, required_tokens):
    key = f"gk_agent_{name.replace('-', '_')}"
    fm, body = frontmatter(GK / "agents" / f"{name}.md")
    if fm is None:
        return fail(key, body)
    for f in ("name", "description"):
        if f not in fm:
            return fail(key, f"frontmatter missing '{f}'")
    for banned in ("WebFetch", "WebSearch"):
        if banned in fm.get("tools", ""):
            return fail(key, f"must not use {banned} (no network)")
    for t in required_tokens:
        if t not in body:
            return fail(key, f"body must reference '{t}'")
    ok(key)


@register("gk_agent_green_guardian")
def _gk_agent_green_guardian():
    _gk_agent("green-guardian", ["anti-fake-green", "revert", "reject"])


@register("gk_agent_fixer")
def _gk_agent_fixer():
    _gk_agent("fixer", ["minimal", "anti-fake-green", "re-run"])


@register("gk_agent_test_writer")
def _gk_agent_test_writer():
    _gk_agent("test-writer", ["test-quality", "behavior", "revert"])


def _gk_cmd(name, required_tokens):
    key = f"gk_cmd_{name.replace('-', '_')}"
    fm, body = frontmatter(GK / "commands" / f"{name}.md")
    if fm is None:
        return fail(key, body)
    if "description" not in fm:
        return fail(key, "frontmatter missing 'description'")
    for t in required_tokens:
        if t not in body:
            return fail(key, f"body must reference '{t}'")
    ok(key)


@register("gk_cmd_green_setup")
def _gk_cmd_green_setup():
    _gk_cmd("green-setup", ["runner-detection", ".green-keeper/config.json"])


@register("gk_cmd_green")
def _gk_cmd_green():
    _gk_cmd("green", ["fixer", "green-guardian", "typecheck", "minimal", "green-setup"])


@register("gk_cmd_cover")
def _gk_cmd_cover():
    _gk_cmd("cover", ["test-writer", "green-guardian", "behavior"])


import os


def _hook_script_ok(key, fname):
    p = GK / "hooks" / fname
    if not p.exists():
        fail(key, f"missing {p}")
        return True
    if not os.access(p, os.X_OK):
        fail(key, f"{fname} is not executable")
        return True
    text = p.read_text()
    for banned in ("curl", "wget", "nc "):
        if banned in text:
            fail(key, f"{fname} must not use network tool '{banned.strip()}'")
            return True
    return None


@register("gk_hook_sessionstart")
def _gk_hook_sessionstart():
    hj, err = load_json(GK / "hooks" / "hooks.json")
    if err:
        return fail("gk_hook_sessionstart", err)
    ss = hj.get("hooks", {}).get("SessionStart")
    if not ss:
        return fail("gk_hook_sessionstart", "hooks.json missing SessionStart")
    if "session-status.sh" not in json.dumps(ss):
        return fail("gk_hook_sessionstart", "SessionStart must call session-status.sh")
    bad = _hook_script_ok("gk_hook_sessionstart", "session-status.sh")
    if bad is not None:
        return
    ok("gk_hook_sessionstart")


@register("gk_hook_stop")
def _gk_hook_stop():
    hj, err = load_json(GK / "hooks" / "hooks.json")
    if err:
        return fail("gk_hook_stop", err)
    st = hj.get("hooks", {}).get("Stop")
    if not st:
        return fail("gk_hook_stop", "hooks.json missing Stop")
    if "check-green.sh" not in json.dumps(st):
        return fail("gk_hook_stop", "Stop must call check-green.sh")
    if _hook_script_ok("gk_hook_stop", "check-green.sh") is not None:
        return
    ok("gk_hook_stop")


@register("gk_hook_posttool")
def _gk_hook_posttool():
    hj, err = load_json(GK / "hooks" / "hooks.json")
    if err:
        return fail("gk_hook_posttool", err)
    pt = hj.get("hooks", {}).get("PostToolUse")
    if not pt:
        return fail("gk_hook_posttool", "hooks.json missing PostToolUse")
    blob = json.dumps(pt)
    if "post-tool-typecheck.sh" not in blob:
        return fail("gk_hook_posttool", "PostToolUse must call post-tool-typecheck.sh")
    if "Edit" not in blob or "Write" not in blob:
        return fail("gk_hook_posttool", "PostToolUse matcher must include Write/Edit")
    if _hook_script_ok("gk_hook_posttool", "post-tool-typecheck.sh") is not None:
        return
    ok("gk_hook_posttool")


@register("gk_readme")
def _gk_readme():
    p = GK / "README.md"
    if not p.exists():
        return fail("gk_readme", f"missing {p}")
    text = p.read_text()
    for token in ("/green", "/green-setup", "no fake-green", ".green-keeper/state"):
        if token not in text:
            return fail("gk_readme", f"README must mention '{token}'")
    ok("gk_readme")


@register("mm_manifest")
def _mm_manifest():
    mkt, err = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    if err:
        return fail("mm_manifest", err)
    plug, err = load_json(MM / ".claude-plugin" / "plugin.json")
    if err:
        return fail("mm_manifest", err)
    if plug.get("name") != "money-map":
        return fail("mm_manifest", "plugin.json name must be 'money-map'")
    for field in ("description", "version"):
        if field not in plug:
            return fail("mm_manifest", f"plugin.json missing '{field}'")
    entry = next((p for p in mkt.get("plugins", []) if p.get("name") == "money-map"), None)
    if entry is None:
        return fail("mm_manifest", "marketplace.json does not list money-map")
    if entry.get("source") != "./money-map":
        return fail("mm_manifest", "money-map source must be './money-map'")
    ok("mm_manifest")


@register("mm_toolkit")
def _mm_toolkit():
    p = MM / "lib" / "moneymap.py"
    if not p.exists():
        return fail("mm_toolkit", f"missing {p}")
    text = p.read_text()
    for sym in ("class Transaction", "def normalize", "def parse", "def categorize",
                "def aggregate", "def anomalies", "def reconcile"):
        if sym not in text:
            return fail("mm_toolkit", f"moneymap.py missing '{sym}'")
    ok("mm_toolkit")


@register("mm_skill_categorization")
def _mm_skill_categorization():
    fm, body = frontmatter(MM / "skills" / "categorization" / "SKILL.md")
    if fm is None:
        return fail("mm_skill_categorization", body)
    if fm.get("name") != "categorization":
        return fail("mm_skill_categorization", "name must be 'categorization'")
    for token in ("categories.json", "rules", "uncategorized"):
        # case-insensitive: SKILL.md uses "Uncategorized" (sentence-initial) vs. the "uncategorized" token
        if token.lower() not in body.lower():
            return fail("mm_skill_categorization", f"body must reference '{token}'")
    ok("mm_skill_categorization")


@register("mm_template")
def _mm_template():
    data, err = load_json(MM / "templates" / "categories.json")
    if err:
        return fail("mm_template", err)
    if not isinstance(data.get("categories"), list) or not isinstance(data.get("rules"), list):
        return fail("mm_template", "categories.json needs 'categories' and 'rules' arrays")
    for r in data["rules"]:
        if "match" not in r or "category" not in r:
            return fail("mm_template", "each rule needs 'match' and 'category'")
    ok("mm_template")


@register("mm_skill_statement_parsing")
def _mm_skill_statement_parsing():
    fm, body = frontmatter(MM / "skills" / "statement-parsing" / "SKILL.md")
    if fm is None:
        return fail("mm_skill_statement_parsing", body)
    if fm.get("name") != "statement-parsing":
        return fail("mm_skill_statement_parsing", "name must be 'statement-parsing'")
    for token in ("mapping", "date_format", "debit", "credit"):
        if token not in body:
            return fail("mm_skill_statement_parsing", f"body must reference '{token}'")
    ok("mm_skill_statement_parsing")


@register("mm_skill_anti_fabrication")
def _mm_skill_anti_fabrication():
    fm, body = frontmatter(MM / "skills" / "anti-fabrication" / "SKILL.md")
    if fm is None:
        return fail("mm_skill_anti_fabrication", body)
    if fm.get("name") != "anti-fabrication":
        return fail("mm_skill_anti_fabrication", "name must be 'anti-fabrication'")
    for token in ("Decimal", "source row", "reconcile"):
        if token not in body:
            return fail("mm_skill_anti_fabrication", f"body must reference '{token}'")
    ok("mm_skill_anti_fabrication")


@register("mm_skill_anomaly_patterns")
def _mm_skill_anomaly_patterns():
    fm, body = frontmatter(MM / "skills" / "anomaly-patterns" / "SKILL.md")
    if fm is None:
        return fail("mm_skill_anomaly_patterns", body)
    if fm.get("name") != "anomaly-patterns":
        return fail("mm_skill_anomaly_patterns", "name must be 'anomaly-patterns'")
    for token in ("duplicate", "recurring", "outlier"):
        # case-insensitive: SKILL.md bolds "Duplicate"/"Outlier" as list headers vs. the lowercase tokens
        if token.lower() not in body.lower():
            return fail("mm_skill_anomaly_patterns", f"body must reference '{token}'")
    ok("mm_skill_anomaly_patterns")


def _mm_agent(name, required_tokens):
    key = f"mm_agent_{name.replace('-', '_')}"
    fm, body = frontmatter(MM / "agents" / f"{name}.md")
    if fm is None:
        return fail(key, body)
    for f in ("name", "description"):
        if f not in fm:
            return fail(key, f"frontmatter missing '{f}'")
    for banned in ("WebFetch", "WebSearch"):
        if banned in fm.get("tools", ""):
            return fail(key, f"must not use {banned} (no network)")
    for t in required_tokens:
        # case-insensitive: subagent bodies bold list headers (e.g. "Source Rows") vs. lowercase tokens
        if t.lower() not in body.lower():
            return fail(key, f"body must reference '{t}'")
    ok(key)


@register("mm_agent_figures_guardian")
def _mm_agent_figures_guardian():
    return _mm_agent("figures-guardian", ["anti-fabrication", "invariant", "source row"])


@register("mm_agent_analyst")
def _mm_agent_analyst():
    return _mm_agent("analyst", ["moneymap", "statement-parsing", "Decimal"])


def _mm_cmd(name, required_tokens):
    key = f"mm_cmd_{name.replace('-', '_')}"
    fm, body = frontmatter(MM / "commands" / f"{name}.md")
    if fm is None:
        return fail(key, body)
    if "description" not in fm:
        return fail(key, "frontmatter missing 'description'")
    for t in required_tokens:
        if t not in body:
            return fail(key, f"body must reference '{t}'")
    ok(key)


@register("mm_cmd_money_setup")
def _mm_cmd_money_setup():
    _mm_cmd("money-setup", ["categories.json", "categorization"])


@register("mm_cmd_understand")
def _mm_cmd_understand():
    _mm_cmd("understand", ["analyst", "figures-guardian", "money/output/", "categorized.csv"])


@register("mm_cmd_reconcile")
def _mm_cmd_reconcile():
    _mm_cmd("reconcile", ["reconcile", "figures-guardian", "only_in"])


@register("mm_cmd_clean")
def _mm_cmd_clean():
    _mm_cmd("clean", ["categorized", "money/output/"])


@register("mm_cmd_report")
def _mm_cmd_report():
    _mm_cmd("report", ["report.md", "figures-guardian"])


@register("mm_readme")
def _mm_readme():
    p = MM / "README.md"
    if not p.exists():
        return fail("mm_readme", f"missing {p}")
    text = p.read_text()
    for token in ("/understand", "/money-setup", "no network", "money/categories.json"):
        if token not in text:
            return fail("mm_readme", f"README must mention '{token}'")
    ok("mm_readme")


# ---- docpin (network plugin: its AGENTS may use WebFetch; the HOOK stays local-only) ----

@register("dp_manifest")
def _dp_manifest():
    mkt, err = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    if err:
        return fail("dp_manifest", err)
    plug, err = load_json(DP / ".claude-plugin" / "plugin.json")
    if err:
        return fail("dp_manifest", err)
    if plug.get("name") != "docpin":
        return fail("dp_manifest", "plugin.json name must be 'docpin'")
    for field in ("description", "version"):
        if field not in plug:
            return fail("dp_manifest", f"plugin.json missing '{field}'")
    entry = next((p for p in mkt.get("plugins", []) if p.get("name") == "docpin"), None)
    if entry is None:
        return fail("dp_manifest", "marketplace.json does not list docpin")
    if entry.get("source") != "./docpin":
        return fail("dp_manifest", "docpin source must be './docpin'")
    ok("dp_manifest")


@register("dp_hook")
def _dp_hook():
    hj, err = load_json(DP / "hooks" / "hooks.json")
    if err:
        return fail("dp_hook", err)
    ss = hj.get("hooks", {}).get("SessionStart")
    if not ss:
        return fail("dp_hook", "hooks.json missing SessionStart")
    blob = json.dumps(ss)
    if "session-start.sh" not in blob:
        return fail("dp_hook", "SessionStart must call session-start.sh")
    if "${CLAUDE_PLUGIN_ROOT}" not in blob:
        return fail("dp_hook", "hook command must use ${CLAUDE_PLUGIN_ROOT}")
    script = DP / "hooks" / "session-start.sh"
    if not script.exists():
        return fail("dp_hook", "missing session-start.sh")
    if not os.access(script, os.X_OK):
        return fail("dp_hook", "session-start.sh is not executable")
    text = script.read_text()
    for banned in ("curl", "wget", "nc "):
        if banned in text:
            return fail("dp_hook", f"session-start.sh must stay local (found '{banned.strip()}')")
    ok("dp_hook")


@register("dp_skill")
def _dp_skill():
    fm, body = frontmatter(DP / "skills" / "docpin" / "SKILL.md")
    if fm is None:
        return fail("dp_skill", body)
    if fm.get("name") != "docpin":
        return fail("dp_skill", "name must be 'docpin'")
    if "description" not in fm:
        return fail("dp_skill", "frontmatter missing 'description'")
    for token in ("resolver", "output-contract", "doc-fetcher", "citation-guardian"):
        if token not in body:
            return fail("dp_skill", f"body must reference '{token}'")
    ok("dp_skill")


def _dp_cmd(name, required_tokens):
    key = f"dp_cmd_{name.replace('-', '_')}"
    fm, body = frontmatter(DP / "commands" / f"{name}.md")
    if fm is None:
        return fail(key, body)
    if "description" not in fm:
        return fail(key, "frontmatter missing 'description'")
    for t in required_tokens:
        if t.lower() not in body.lower():
            return fail(key, f"body must reference '{t}'")
    ok(key)


@register("dp_cmd_docs")
def _dp_cmd_docs():
    _dp_cmd("docs", ["Source"])


@register("dp_cmd_docs_scan")
def _dp_cmd_docs_scan():
    _dp_cmd("docs-scan", ["resolvable"])


@register("dp_cmd_docs_setup")
def _dp_cmd_docs_setup():
    _dp_cmd("docs-setup", [".docpin/config.json"])


def _dp_agent(name, required_tokens):
    # docpin is a network plugin: unlike the local plugins, its agents MAY declare WebFetch.
    key = f"dp_agent_{name.replace('-', '_')}"
    fm, body = frontmatter(DP / "agents" / f"{name}.md")
    if fm is None:
        return fail(key, body)
    for f in ("name", "description"):
        if f not in fm:
            return fail(key, f"frontmatter missing '{f}'")
    for t in required_tokens:
        if t.lower() not in body.lower():
            return fail(key, f"body must reference '{t}'")
    ok(key)


@register("dp_agent_doc_fetcher")
def _dp_agent_doc_fetcher():
    _dp_agent("doc-fetcher", ["resolve", "Source", "distill"])


@register("dp_agent_citation_guardian")
def _dp_agent_citation_guardian():
    _dp_agent("citation-guardian", ["version", "citation", "reject"])


@register("dp_readme")
def _dp_readme():
    p = DP / "README.md"
    if not p.exists():
        return fail("dp_readme", f"missing {p}")
    text = p.read_text()
    for token in ("/docs", "docpin@localplugins", "version-matched"):
        if token not in text:
            return fail("dp_readme", f"README must mention '{token}'")
    ok("dp_readme")


# ---- brand-forge (vector core is local; the opt-in raster engine lives in lib/, not the hook/agents) ----

@register("bf_manifest")
def _bf_manifest():
    mkt, err = load_json(ROOT / ".claude-plugin" / "marketplace.json")
    if err:
        return fail("bf_manifest", err)
    plug, err = load_json(BF / ".claude-plugin" / "plugin.json")
    if err:
        return fail("bf_manifest", err)
    if plug.get("name") != "brand-forge":
        return fail("bf_manifest", "plugin.json name must be 'brand-forge'")
    for field in ("description", "version"):
        if field not in plug:
            return fail("bf_manifest", f"plugin.json missing '{field}'")
    entry = next((p for p in mkt.get("plugins", []) if p.get("name") == "brand-forge"), None)
    if entry is None:
        return fail("bf_manifest", "marketplace.json does not list brand-forge")
    if entry.get("source") != "./brand-forge":
        return fail("bf_manifest", "brand-forge source must be './brand-forge'")
    ok("bf_manifest")


@register("bf_hook")
def _bf_hook():
    hj, err = load_json(BF / "hooks" / "hooks.json")
    if err:
        return fail("bf_hook", err)
    ss = hj.get("hooks", {}).get("SessionStart")
    if not ss:
        return fail("bf_hook", "hooks.json missing SessionStart")
    blob = json.dumps(ss)
    if "session-start.sh" not in blob:
        return fail("bf_hook", "SessionStart must call session-start.sh")
    if "${CLAUDE_PLUGIN_ROOT}" not in blob:
        return fail("bf_hook", "hook command must use ${CLAUDE_PLUGIN_ROOT}")
    script = BF / "hooks" / "session-start.sh"
    if not script.exists():
        return fail("bf_hook", "missing session-start.sh")
    if not os.access(script, os.X_OK):
        return fail("bf_hook", "session-start.sh is not executable")
    text = script.read_text()
    for banned in ("curl", "wget", "nc "):
        if banned in text:
            return fail("bf_hook", f"session-start.sh must stay local (found '{banned.strip()}')")
    ok("bf_hook")


def _bf_agent(name):
    key = f"bf_agent_{name.replace('-', '_')}"
    fm, body = frontmatter(BF / "agents" / f"{name}.md")
    if fm is None:
        return fail(key, body)
    for f in ("name", "description"):
        if f not in fm:
            return fail(key, f"frontmatter missing '{f}'")
    # brand-forge's agents are local (art-director designs, visual-guardian checks read-only)
    for banned in ("WebFetch", "WebSearch"):
        if banned in fm.get("tools", ""):
            return fail(key, f"must not use {banned} (agents are local)")
    ok(key)


@register("bf_agent_art_director")
def _bf_agent_art_director():
    _bf_agent("art-director")


@register("bf_agent_visual_guardian")
def _bf_agent_visual_guardian():
    _bf_agent("visual-guardian")


@register("bf_skills")
def _bf_skills():
    for s in ("generate-doc-template", "generate-graphic", "generate-logo", "generate-social"):
        fm, body = frontmatter(BF / "skills" / s / "SKILL.md")
        if fm is None:
            return fail("bf_skills", body)
        if fm.get("name") != s:
            return fail("bf_skills", f"{s} SKILL.md name must be '{s}'")
        if "description" not in fm:
            return fail("bf_skills", f"{s} missing description")
    ok("bf_skills")


def _bf_cmd(name):
    key = f"bf_cmd_{name.replace('-', '_')}"
    fm, body = frontmatter(BF / "commands" / f"{name}.md")
    if fm is None:
        return fail(key, body)
    if "description" not in fm:
        return fail(key, "frontmatter missing 'description'")
    ok(key)


@register("bf_cmd_brand_new")
def _bf_cmd_brand_new():
    _bf_cmd("brand-new")


@register("bf_cmd_brand_make")
def _bf_cmd_brand_make():
    _bf_cmd("brand-make")


@register("bf_cmd_brand_status")
def _bf_cmd_brand_status():
    _bf_cmd("brand-status")


@register("bf_cmd_brand_use")
def _bf_cmd_brand_use():
    _bf_cmd("brand-use")


@register("bf_cmd_brand_export")
def _bf_cmd_brand_export():
    _bf_cmd("brand-export")


@register("bf_readme")
def _bf_readme():
    p = BF / "README.md"
    if not p.exists():
        return fail("bf_readme", f"missing {p}")
    text = p.read_text()
    for token in ("/brand-new", "brand-forge@localplugins"):
        if token not in text:
            return fail("bf_readme", f"README must mention '{token}'")
    ok("bf_readme")


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else None
    names = [which] if which else list(CHECKS)
    for n in names:
        if n not in CHECKS:
            print(f"FAIL: unknown check '{n}'")
            sys.exit(2)
        CHECKS[n]()
    sys.exit(1 if FAILURES else 0)


if __name__ == "__main__":
    main()
