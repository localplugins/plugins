# output-contract.md — distillation, citation, and honesty rules

This is the contract every grounded answer must satisfy once step 4 of the
resolve → fetch → ground loop (`resolver.md`) has fetched version-pinned docs.
It governs how the fetched material becomes the final answer.

## 1. Distill, don't dump

After fetching a doc source, extract **only the sections relevant to the
topic/task** — the signature, the specific option or method being asked
about, a minimal usage example. Do not paste the entire fetched page back at
the user; a version-pinned fetch is an input to the answer, not the answer
itself.

## 2. Always cite

Every answer that used a version-pinned fetch must end with a `Source:` line
that names:

1. The resolved package and version actually used (`<pkg>@<version>`), and
2. The exact URL(s) fetched.

This is how the user can verify the answer without re-deriving it. Cite even
when the answer is short — a one-line code suggestion still needs a citing
`Source:` line so the version basis is never implicit.

```
Source: react@18.2.0 — https://raw.githubusercontent.com/facebook/react/v18.2.0/README.md
```

Multiple sources are listed on separate lines under the same `Source:`
heading, or as additional `Source:` lines — either is fine as long as each
URL fetched is named.

## 3. Absent symbol → say so, never fabricate

If the requested symbol, method, option, or API is **not present** in the
resolved version's docs, state that plainly:

```
useFooBar is not present in react@17.0.2.
```

Do not guess a plausible-looking signature, do not silently answer as if the
symbol existed in a later version, and do not quietly substitute a similarly
named symbol without flagging the substitution. When in doubt, say what
*is* present in that version instead of inventing what isn't.

## 4. Label the version basis on any fallback

When resolution didn't land on an exact version-pinned match (see
`resolver.md` §5, Fallback), the answer must label the basis of the version
it did use — verbatim one of:

- `latest (unpinned)` — no lockfile, or the version couldn't be resolved, so
  the latest published version was used instead.
- `closest available (<v>)` — the exact pinned version had no doc build; a
  nearby version `<v>` was used instead.
- `local bundled` — the registry lookup failed (private/unpublished package)
  and the locally installed copy's bundled docs were used instead.

Never present a fallback result as if it were the exact version-pinned
match — the label must appear alongside the citation, not be silently
dropped.

## 5. Before / after example

**Before (not compliant — no citation, invents a symbol):**

> Use `axios.retry(config)` to add automatic retries.

This both fabricates a method that doesn't exist on the `axios` default
export and gives the user no way to check the claim.

**After (compliant):**

> `axios` itself has no built-in `retry` option in `axios@1.6.7` — retries
> need the separate `axios-retry` package, or a manual interceptor. Here's
> the manual interceptor form:
>
> ```js
> axios.interceptors.response.use(undefined, (err) => { /* retry logic */ });
> ```
>
> `axios.retry(config)` is not present in `axios@1.6.7`.
>
> Source: axios@1.6.7 — https://raw.githubusercontent.com/axios/axios/v1.6.7/README.md
