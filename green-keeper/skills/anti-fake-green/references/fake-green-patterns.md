# Fake-green vs. real-fix patterns

Every example below shows a red check, the **fake-green** move that makes it pass without fixing anything, and the **real fix** that makes it pass for the right reason. Use these to recognize a cheat in a diff and to choose the legitimate change.

The principle in one line: **the failing check is a signal about the code — fix the code, not the signal.**

---

## JavaScript / TypeScript

### A failing test

Suppose `discount(100, 0.2)` should return `80` but returns `120` (the code adds instead of subtracts).

```js
// FAILING TEST
test("applies a 20% discount", () => {
  expect(discount(100, 0.2)).toBe(80);
});
```

**Fake-green — do NOT do these:**

```js
test.skip("applies a 20% discount", () => { ... });        // removed the test
it.only("something else", () => { ... });                   // silently disables siblings
expect(discount(100, 0.2)).toBeTruthy();                    // weakened: 120 is truthy
expect(discount(100, 0.2)).toBe(120);                       // bent the test to the bug
```

**Real fix — correct the production code:**

```js
// discount.js
export function discount(price, rate) {
  return price - price * rate;   // was: price + price * rate
}
```

The test is unchanged; the bug is gone.

### A type error

```ts
function totalCents(items: Item[]): number {
  return items.reduce((sum, i) => sum + i.priceCents, 0);
}
totalCents(getItems());   // Type error: getItems() returns Item[] | undefined
```

**Fake-green:**

```ts
totalCents(getItems() as any);          // widened to any — error silenced
// @ts-ignore                            // suppressed the compiler
totalCents(getItems());
```

**Real fix — handle the real case the type is warning you about:**

```ts
const items = getItems();
if (items) totalCents(items);
// or, if absence is truly impossible, narrow honestly:
totalCents(getItems() ?? []);
```

---

## Python

### A failing test

`parse_bool("no")` should be `False` but returns `True`.

**Fake-green:**

```python
@pytest.mark.skip(reason="flaky")     # removed the test
def test_parse_bool_no(): ...

def test_parse_bool_no():
    assert parse_bool("no") is not None   # weakened: any non-None passes

def test_parse_bool_no():
    assert parse_bool("no") is True       # bent the test to the bug
```

**Real fix:**

```python
def parse_bool(s: str) -> bool:
    return s.strip().lower() in {"1", "true", "yes", "y"}   # "no" -> False
```

### A silenced exception

```python
def load_config(path):
    try:
        return json.loads(Path(path).read_text())
    except Exception:
        pass          # FAKE-GREEN: swallows the real failure, returns None silently
```

**Real fix — let the caller know, or handle the specific case:**

```python
def load_config(path):
    try:
        return json.loads(Path(path).read_text())
    except FileNotFoundError:
        return DEFAULT_CONFIG            # a real, intended fallback
```

### A type-check error (mypy/pyright)

**Fake-green:**

```python
result = compute(x)  # type: ignore    # suppressed the type checker
```

**Real fix — make the types honest:**

```python
result = compute(x) if x is not None else 0
```

---

## Go

### A failing test

`Sum([]int{})` should return `0`, but the code panics on an empty slice.

**Fake-green:**

```go
func TestSumEmpty(t *testing.T) {
    t.Skip("todo")                       // removed the test
}

func TestSumEmpty(t *testing.T) {
    _ = Sum([]int{})                     // asserts nothing
}
```

**Real fix:**

```go
func Sum(xs []int) int {
    total := 0
    for _, x := range xs { total += x }  // handles empty naturally
    return total
}
```

### A compile / vet error

**Fake-green — commenting out the offending call or using `_ = x` to dodge "declared but not used" without addressing why it's unused.** If the variable should be used, use it; if it's genuinely dead, delete it.

**Real fix:**

```go
// Remove the dead computation entirely, or wire its result into the return.
```

---

## Rust

### A failing test

`checked_div(10, 0)` should return `None`, but the code divides directly and panics.

**Fake-green:**

```rust
#[test]
#[ignore]                                 // removed the test
fn divides_by_zero() { ... }

#[test]
fn divides_by_zero() {
    let _ = checked_div(10, 0);           // asserts nothing
}
```

**Real fix:**

```rust
fn checked_div(a: i32, b: i32) -> Option<i32> {
    if b == 0 { None } else { Some(a / b) }
}
```

### A compile error (borrow/type)

**Fake-green:** reaching for `unsafe`, an unnecessary `.clone()` to dodge a borrow you don't understand, or `#[allow(...)]` to mute a real warning.

**Real fix:** restructure ownership so the borrow is valid, or make the type match. If a `.clone()` is genuinely the right call (you need an owned copy), it's fine — the test is whether it addresses the cause or just mutes the compiler.

---

## The rejection catalog (what `green-guardian` looks for in a diff)

Reject the change if the diff does any of the following:

| Category | Signals to grep for |
| --- | --- |
| Removed test | `.skip`, `.only`, `xit`, `xdescribe`, `fdescribe`, `@pytest.mark.skip`, `t.Skip`, `#[ignore]`, commented-out `test`/`it`/`def test_` blocks |
| Weakened assertion | `toBeTruthy`/`toBeDefined` replacing an exact matcher, removed `expect`/`assert` lines, `assert x is not None` replacing a value check, broadened matchers |
| Silenced error | `@ts-ignore`, `@ts-expect-error` used to hide (not document), `eslint-disable`, `# type: ignore`, `# noqa`, empty `catch {}`, `except ...: pass`, `#[allow(...)]`, `_ =` used to dodge unused-var checks |
| Widened type | new `any` / `unknown` / `object` / `interface{}` / `Box<dyn Any>` introduced only to clear an error |
| Padded coverage | new tests with no assertion, or asserting only that a mock/spy was called with no output check |
| Test bent to bug | a *test* file changed (expected values altered) when the production code was the thing at fault |

When a diff touches both a test and production code, ask: *which one was actually wrong?* If the production code was wrong, the expected values in the test must not have moved.

## When you genuinely cannot make it green

Some red needs a human or product decision — an ambiguous spec, a missing credential you must not fabricate, a design choice about behavior. In that case:

1. Do **not** skip, silence, or weaken anything to make the red disappear.
2. Report the failing item, the root cause you found, and the specific decision required.
3. Leave it red and visible. Honest red beats hidden bugs.
