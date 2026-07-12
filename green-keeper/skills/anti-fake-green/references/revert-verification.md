# Revert-verification: proving a fix or test is real

Revert-verification is the proof that green means correct. The idea is simple: a fix only counts if **undoing it brings the red back**, and a new test only counts if it **fails on the old code and passes on the new**. If a test passes whether or not your change is present, it proves nothing.

Two procedures follow — one for a fix to failing code, one for a new or changed test.

---

## Procedure A — verify a fix to failing code/tests

You changed production code to make a failing check pass. Prove the change is what fixed it.

1. **Confirm green now.** Run the relevant test and the typecheck (commands from `.green-keeper/config.json`). Both must pass.
2. **Revert only your production change.** Keep the test as-is. Options:
   - Stash just the changed file: `git stash push -- <path/to/changed/file>`
   - Or check out the pre-change version: `git checkout HEAD -- <path/to/changed/file>` (only if it was committed clean before).
3. **Re-run the check.** It must go **red again** — the same failure you started with. This proves your change caused the fix.
4. **Restore your fix.** `git stash pop` (or re-apply your edit).
5. **Confirm green again.** Re-run; it must pass.

If step 3 stays green after reverting, your change was not what fixed it (something else did, or the test never exercised the code path). Investigate before claiming success.

---

## Procedure B — verify a new or changed test

You wrote a test for changed behavior. Prove the test actually exercises that change.

1. **Confirm the test passes** against the current (changed) code.
2. **Revert the production change, keep the new test.**
   - Stash only the production file(s): `git stash push -- <src file(s)>` — leave the test file out of the stash so it stays on disk.
   - If the production change is already committed, temporarily check out its parent: `git checkout HEAD~1 -- <src file>` (then restore afterward).
3. **Run the new test against the old code.** It must **fail**. That failure is the proof the test targets the new behavior.
4. **Restore the production change.** `git stash pop` (or re-checkout the current file).
5. **Run the test again.** It must **pass**.

A test that passes in both step 3 and step 5 is not testing your change — rewrite it to assert the specific new behavior, then repeat.

---

## Commands cheat-sheet

```bash
# Stash a single file (keep everything else on disk)
git stash push -- path/to/file

# Bring it back
git stash pop

# Restore one file to its committed state
git checkout HEAD -- path/to/file

# Look at one file from a previous commit without touching the tree
git show HEAD~1:path/to/file
```

Prefer per-file stashing over a blanket `git stash` so you isolate exactly the change under test and don't disturb unrelated edits.

---

## Pitfalls

- **Stashing the test along with the fix.** If you stash both, step 3 has no test to run. Stash only the *production* file when verifying a test; stash only the *fix* file when verifying a fix.
- **Cached builds or test artifacts.** Some toolchains cache compiled output; a stale cache can mask the revert. Force a clean run if results look impossible (e.g. `cargo test` after `cargo clean`, `pytest -p no:cacheprovider`, delete `.tsbuildinfo`).
- **Non-deterministic tests.** If a test passes or fails at random, revert-verification is meaningless — fix the flakiness (time, ordering, randomness, network) first. See the `test-quality` skill.
- **Multiple intertwined changes.** If one edit fixes several failures, revert-verify each failure maps to the change. If reverting the change only brings some failures back, the others had a different cause.
- **Uncommitted baseline.** Procedures using `git checkout HEAD --` assume the file was clean before you started. If it wasn't, use stashing instead so you don't lose unrelated work.

## What to report

After verification, state plainly:

- **For a fix:** "Reverting `<file>` reproduces `<failure>`; re-applying makes `<test>` and typecheck pass."
- **For a test:** "`<test>` fails on the pre-change code (`<failure>`) and passes on the change."

If verification did not behave as expected, say so — do not claim green you could not prove.
