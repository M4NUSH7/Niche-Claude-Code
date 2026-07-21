# Keeping the graph current: update, cluster-only, watch (adapted from
# graphify's references/update.md and references/add-watch.md, commit c83085c)

Read this when the graph already exists and the source changed, or you want
it to stay current automatically during a session.

## graphify update - incremental re-extraction

```bash
graphify update <path>
graphify update <path> --no-cluster   # skip Leiden clustering, raw extraction only (faster)
graphify update <path> --force        # overwrite graph.json even if the rebuild has fewer nodes
```

This is the build step this skill uses - it re-extracts code files via
tree-sitter AST (deterministic, no LLM, nothing leaves the machine) and
writes/refreshes `<path>/graphify-out/graph.json`. Only changed files are
re-extracted on repeat runs (content-hash cache) - `update` is cheap to
re-run after every edit wave.

`--force` matters after a refactor that deletes code: without it, graphify
refuses to shrink an existing `graph.json` (a smaller rebuild looks like a
failed extraction otherwise). Use `--force` when you know the shrink is
real.

`--no-cluster` skips community detection (Leiden) - use it for a fast
rebuild, or on a corpus too small for clustering to be meaningful. Add
clustering back on a later full run when you want community labels in
`GRAPH_REPORT.md`.

## graphify cluster-only - re-cluster without re-extracting

```bash
graphify cluster-only <path>
```

Re-runs clustering and regenerates `GRAPH_REPORT.md` / `graph.json` /
`graph.html` from the existing graph, without touching extraction. Use this
if you built with `--no-cluster` and later want community labels, and
nothing in the source changed.

## graphify watch - auto-rebuild during a session

```bash
graphify watch <path>
```

Watches a folder and rebuilds the graph automatically as code changes -
debounced, so a burst of edits triggers one rebuild, not one per file.
Code-only changes are free (AST, no LLM); doc/paper/image changes need the
LLM semantic pass and are flagged rather than rebuilt silently. Run it in a
background terminal for the duration of a working session so the graph
never goes stale; Ctrl+C to stop.

## Order of operations for a fresh graph

1. `graphify update <repo>` (first run: full build)
2. `graphify watch <repo>` in a background terminal, if the session will
   span multiple edit waves
3. `graphify query` / `path` / `explain` against `graphify-out/graph.json`
   as questions come up - no re-reading source files needed
4. `graphify update <repo>` again (or rely on `watch`) whenever files change
   outside the watched session
