# Good-vs-bad test patterns

A test earns its place by catching a real regression and documenting intended behavior. Below are the patterns that make a test worth keeping, each with a weak version and a strong version.

---

## Behavior over implementation

Assert what the code *produces*, not how it's wired. Implementation-coupled tests break on harmless refactors and pass through real bugs.

**Weak — couples to internals:**

```js
test("adds item", () => {
  const cart = new Cart();
  const spy = jest.spyOn(cart, "_recalculate");
  cart.add(item);
  expect(spy).toHaveBeenCalled();        // tests a private method, not the outcome
});
```

**Strong — asserts observable behavior:**

```js
test("adding an item updates the total", () => {
  const cart = new Cart();
  cart.add({ priceCents: 500 });
  expect(cart.totalCents()).toBe(500);   // the behavior a user cares about
});
```

If `_recalculate` is renamed or inlined, the weak test breaks for no reason; the strong one keeps working. If the total math breaks, the weak test still passes; the strong one fails.

---

## Narrowest assertion that captures intent

Exact expectations catch more bugs than loose ones.

```python
# Weak: 120, -3, and 999 all pass
assert discount(100, 0.2) is not None

# Strong: only the correct answer passes
assert discount(100, 0.2) == 80
```

`toBeTruthy`, `toBeDefined`, `is not None`, and `assert result` are red flags when a specific value is knowable. Use them only when the value genuinely isn't (e.g. asserting a non-empty generated id).

---

## Edge cases that actually occur

Cover the critical path first, then the boundaries that real inputs hit.

```go
func TestSum(t *testing.T) {
    cases := []struct{ name string; in []int; want int }{
        {"typical", []int{1, 2, 3}, 6},
        {"empty", []int{}, 0},              // boundary that really happens
        {"single", []int{7}, 7},
        {"negatives", []int{-2, 5}, 3},     // real input, real bug surface
    }
    for _, c := range cases {
        if got := Sum(c.in); got != c.want {
            t.Errorf("%s: Sum(%v) = %d, want %d", c.name, c.in, got, c.want)
        }
    }
}
```

Choose edge cases by asking "what input has actually broken this kind of code?" — empty, null, zero, boundary values, error paths, off-by-one. Don't pad with impossible inputs.

---

## One behavior per test

Split so a failure localizes the bug. A ten-assertion test tells you *something* broke; four focused tests tell you *what*.

**Weak:**

```python
def test_user():
    u = create_user("a@b.com", "pw")
    assert u.email == "a@b.com"
    assert u.is_active is True
    assert u.role == "member"
    assert login(u, "pw") is True
    assert login(u, "wrong") is False
```

**Strong:**

```python
def test_new_user_is_active(): ...
def test_new_user_defaults_to_member_role(): ...
def test_login_succeeds_with_correct_password(): ...
def test_login_fails_with_wrong_password(): ...
```

Each name reads as a spec line, and one failure points straight at the broken behavior.

---

## Determinism: control time, order, and randomness

A test that flakes can't be revert-verified and erodes trust in the suite.

**Weak — depends on the wall clock:**

```js
test("token expires in an hour", () => {
  const t = issueToken();
  expect(t.expiresAt).toBe(Date.now() + 3600_000);   // races the real clock
});
```

**Strong — inject or freeze time:**

```js
test("token expires one hour after issue", () => {
  jest.useFakeTimers().setSystemTime(new Date("2026-01-01T00:00:00Z"));
  const t = issueToken();
  expect(t.expiresAt).toBe(Date.parse("2026-01-01T01:00:00Z"));
});
```

The same applies to random seeds (seed them), collection ordering (sort before asserting, or assert as a set), and network (don't — see below).

---

## Right-sized mocking

Mock the boundary (network, filesystem, clock), not the thing under test. A test that only checks a mock was called tests nothing real.

**Weak — mock-testing-mocks:**

```python
def test_fetch_user():
    api = Mock()
    api.get.return_value = {"id": 1}
    get_user(api, 1)
    api.get.assert_called_with("/users/1")   # asserts the call, not the result
```

**Strong — assert the real output the code derives:**

```python
def test_fetch_user_returns_domain_object():
    api = Mock()
    api.get.return_value = {"id": 1, "email": "a@b.com"}
    user = get_user(api, 1)
    assert user.email == "a@b.com"           # the behavior get_user is responsible for
```

Mock the HTTP client (a real boundary); assert the object `get_user` builds. If `get_user`'s mapping logic breaks, the strong test fails; the weak one doesn't.

---

## Snapshots are not a substitute for assertions

A snapshot captures whatever the code currently emits — including a bug — and "passes" until someone eyeballs a diff. Use snapshots for large, stable output (rendered markup) where a targeted assertion is impractical, and always pair them with at least one meaningful explicit assertion about the behavior that matters. Never reach for a snapshot to avoid deciding what the correct value is.

---

## Rust example — behavior and a real edge case

```rust
#[test]
fn checked_div_returns_quotient() {
    assert_eq!(checked_div(10, 2), Some(5));
}

#[test]
fn checked_div_returns_none_on_zero_divisor() {
    assert_eq!(checked_div(10, 0), None);   // the edge case that would otherwise panic
}
```

Two focused tests, exact expectations, named for the behavior — each fails loudly if that behavior regresses.

---

## Match the project

Before writing, find where sibling tests live and copy their conventions: framework (`vitest`/`jest`/`pytest`/`go test`/`cargo test`), file location (`__tests__/`, `*_test.go`, `tests/`), naming, and setup/fixture style. A well-placed test that reads like its neighbors is one the team will maintain; an orphan in the wrong style rots.
