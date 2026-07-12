# caching.md — cache format and invalidation

A project-local, opt-out cache of fetched/distilled docs, so repeated
questions about the same pinned `pkg@version` don't re-fetch over the
network. This is the caching step (after a successful fetch) of the
resolve → fetch → ground loop (`resolver.md`).

## Cache key and location

Cached entries are plain text (Markdown) files under the project-local cache
directory (default `.docpin/cache`, configurable via `.docpin/config.json`
→ `cache.dir`), keyed by ecosystem, package, and exact version:

```
.docpin/cache/<ecosystem>/<pkg>@<version>[/topic].md
```

- `<ecosystem>` — one of `npm`, `pypi`, `crates`, `go`.
- `<pkg>@<version>` — the resolved package name and the exact version used
  (including any fallback basis noted in the distilled content itself —
  see `output-contract.md` §4).
- `[/topic]` — optional; when the fetch was scoped to a specific
  topic/symbol, the distilled result for that topic is cached under its own
  file so unrelated topics for the same `pkg@version` don't collide or grow
  one giant cache entry.

Example: a topic-scoped lookup for serde's `Deserializer` trait at
`1.0.196` caches to `.docpin/cache/crates/serde@1.0.196/deserializer.md`; an
untopic-scoped fetch of the same version caches to
`.docpin/cache/crates/serde@1.0.196.md`.

## Read path: check cache first

On every request, before doing a registry lookup or a doc fetch, check
whether `.docpin/cache/<ecosystem>/<pkg>@<version>[/topic].md` already
exists. On a cache hit, reuse the cached, already-distilled content directly
— skip the network fetch entirely and cite it exactly as if freshly fetched
(the citation is unaffected by whether the content came from cache or a live
fetch).

## Write path: write-through after a successful fetch

After a successful live fetch and distillation (steps 3–5 of the resolve →
fetch → ground loop), write the distilled result through to the
corresponding cache file before returning the answer. A failed or partial
fetch is never cached — only a successful, cite-able result is persisted.

## Self-invalidation via the version in the key

There is no separate expiry or invalidation step. Because the exact
resolved version is part of the cache key, a stale entry simply stops being
the one that gets looked up the moment the project's pin changes: bumping
`serde` from `1.0.196` to `1.0.197` means the next request looks up
`serde@1.0.197`, a different (and initially absent) cache key, so the old
`1.0.196` entry is never read again. It can be left in place harmlessly or
pruned; docpin doesn't need to actively delete it for correctness.

## Honoring `cache.enabled=false`

When `.docpin/config.json` sets `cache.enabled` to `false` (default is
`true`), skip both the read path and the write path entirely: never check
for a cache hit, and never write a fetched result to disk. Every request
behaves as a fresh fetch, and no cache files are created or read while
disabled.

## Git-ignored

`.docpin/cache/` holds derived, re-fetchable content keyed to versions
already recorded in the project's own lockfiles — it is not source and
should never be committed. The directory is git-ignored by default.
