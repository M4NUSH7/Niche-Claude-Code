---
name: graphify
description: Use for codebase comprehension - navigating an unfamiliar or large repo, understanding how code connects, building a call/import graph, answering "where is X used" or "what calls Y", or tracing a path between two functions/modules - instead of blind grep+read loops that re-read the same files every turn. Builds a queryable code graph once (graphify update), then answers via graphify query/path/explain against that graph. Not an agent orchestration engine (it maps CODE structure, not agent workflows); not for web scraping or general data collection.
allowed-tools: Bash, Read, Grep, Glob
---

# graphify: query a code graph instead of re-reading files

graphify (CLI, already installed via `uv tool install graphifyy`) parses a
repo with tree-sitter into a graph of nodes (functions, classes, files,
concepts) and edges (`calls`, `imports`, `implements`, ...), each tagged
`EXTRACTED` (explicit in source) or `INFERRED` (derived). Build the graph
once, then navigate it with cheap traversal queries instead of dumping whole
files into context on every question.

Use this instead of repeated grep+read cycles when: exploring an unfamiliar
codebase, answering "how does X connect to Y", finding every caller of a
function, or tracing a dependency chain across files.

## Workflow

### 1. Build the graph once

```bash
graphify update <repo-path> --no-cluster   # fast: skip community clustering
graphify update <repo-path>                # with clustering (adds community labels to the report)
```

This is the build step - despite the name, `update` does the initial build
*and* every incremental refresh afterward (only changed files are
re-extracted on repeat runs). Code extraction is pure tree-sitter AST: no
LLM, no API key, nothing leaves the machine. Output lands at the default
location:

```
<repo-path>/graphify-out/graph.json
```

Pass `--force` if a later `update` needs to shrink the graph (e.g. after
deleting a lot of code) - graphify otherwise refuses to overwrite a bigger
graph with a smaller one. Details, plus `cluster-only` and `watch`:
`references/update-and-watch.md`.

### 2. Navigate without re-reading files

```bash
graphify query "how does authentication work" --graph <repo-path>/graphify-out/graph.json
graphify path "AuthModule" "Database" --graph <repo-path>/graphify-out/graph.json
graphify explain "AuthModule" --graph <repo-path>/graphify-out/graph.json
```

- `query "<question>"` - BFS traversal (default) for broad "what connects to
  X" context, or `--dfs` to trace one chain deep. `--budget N` caps output
  tokens (default 2000).
- `path "A" "B"` - shortest route between two named nodes, with each hop's
  relation and confidence tag. Example real output:
  ```
  Shortest path (3 hops):
    FastAPI --uses--> DefaultPlaceholder <--references-- get_request_handler() --references--> ModelField
  ```
- `explain "X"` - the node plus every neighbor, relation, and confidence
  tag. Example: `explain "helper"` on a 2-file fixture returned the node at
  `pkg/a.py L1` together with its connections - this is the smoke-tested
  shape of the output.

The token win is the point: once `graph.json` exists, answering "where is
this used" is one `query`/`explain` call against a compact graph, not
re-reading every candidate file. Full semantics (vocabulary-expansion trick
for when your wording doesn't match the graph's labels, DFS vs BFS
tradeoffs, the optional `save-result`/`reflect` memory loop): read
`references/query-path-explain.md` before running a query that returns
nothing or looks wrong - the fix is almost always wording, not a missing
graph.

### 3. Keep it current

```bash
graphify watch <repo-path>
```

Run in a background terminal for the session; it debounces and rebuilds
automatically as code changes so the graph doesn't go stale mid-session.
Details: `references/update-and-watch.md`.

## Setup (already done on this machine)

- CLI: `uv tool install graphifyy` (installs both `graphify` and
  `graphify-mcp` on PATH). `scoop` is only relevant for a missing
  Python/uv prerequisite - graphify itself is a pip/uv package, not a scoop
  package, and has no desktop app.
- Functional smoke already confirmed: `graphify update` on a 2-file fixture
  built 4 nodes / 5 edges; `graphify explain "helper"` returned the node at
  `pkg/a.py L1` with its connections.

**Do not run `graphify install` (or any per-platform `graphify <host>
install`, e.g. `graphify claude install`) in a harness project.** That
command rewrites `~/.claude/CLAUDE.md` and installs its own PreToolUse hook
- it collides with `init-harness`'s `sync_harness` ownership of those same
files. This skill's workflow only needs `update` / `query` / `path` /
`explain` / `watch`, none of which touch CLAUDE.md or hooks. If a project
genuinely wants the native slash-command integration, register the content
manually (copy what's needed, don't run the installer) so harness ownership
stays intact.

## Optional: MCP server

`graphify-mcp` also exists as an MCP server exposing the same graph as
live tools (`query_graph`, `get_node`, `get_neighbors`, `shortest_path`,
etc.) for an agent orchestrator that prefers tool calls over shelling out.
It is not wired into this skill - see `references/exports-and-mcp.md` for
how to register it if a project wants that path.

## References

| File | Read it when |
|---|---|
| `references/query-path-explain.md` | A `query`/`path`/`explain` call returns nothing, looks wrong, or you want the vocabulary-expansion trick, BFS/DFS tradeoffs, or the optional save-result/reflect memory loop |
| `references/update-and-watch.md` | Details on `update`, `--force`, `--no-cluster`, `cluster-only`, and `watch` debounce behavior |
| `references/exports-and-mcp.md` | Exporting to SVG/GraphML/Neo4j/FalkorDB, or registering the `graphify-mcp` server |
| `references/how-it-works.md` | What `update` actually did internally (tree-sitter passes, confidence tagging, the `graph.json` schema) - read to interpret a node/edge field |
| `references/architecture.md` | Module-by-module internals of the graphify library itself (only relevant if extending graphify's own extractors, not for using it) |
