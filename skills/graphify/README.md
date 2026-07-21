# graphify

**Navigate a codebase via a queryable relational map instead of blind grep+read loops.**

## What it does

Builds a code knowledge-graph once (tree-sitter AST -> nodes = functions/concepts, edges = calls/imports/uses) and then answers navigation questions against that graph - so the agent stops re-reading the same files every turn.

CLI surface:

| Command | Does |
|---|---|
| `graphify update <path>` | Build/refresh the graph into `graphify-out/graph.json` (no LLM needed) |
| `graphify query "<question>"` | BFS traversal answering a question over the graph |
| `graphify path "A" "B"` | Shortest path between two nodes (a call chain) |
| `graphify explain "X"` | Plain-language explanation of a node and its neighbors/edges |
| `graphify watch <path>` | Auto-rebuild on code changes |

## Why it works

Blind `grep` + full-file reads re-inject the same context into the agent's window repeatedly - expensive and lossy on large or unfamiliar repos. A relational map is built once and then *queried*: "where is X used", "what calls Y", "trace a path from A to B" become graph lookups, not file dumps. This pairs directly with harness Goal Packets - a handoff's `inputs` can point at graph queries instead of a list of files.

## How to use

Fires on codebase-comprehension asks: navigating an unfamiliar/large repo, understanding how code connects, "where is X used", tracing between functions. It maps **code structure** - it is not an agent-orchestration engine and not for web scraping.

Install (cross-platform): `uv tool install graphifyy` (pip package; not a scoop package, no desktop app). **Do not** run `graphify install` in a harness project - it rewrites account/agent config and collides with a harness that owns those files.

## Key files

| Path | Purpose |
|---|---|
| `SKILL.md` | The build-once-then-query workflow + install |
| `references/query-path-explain.md` | The navigation command semantics |
| `references/update-and-watch.md` | Building and keeping the graph current |
| `references/exports-and-mcp.md` | SVG/GraphML/Neo4j export + the `graphify-mcp` server |
| `references/architecture.md` / `how-it-works.md` | The extraction pipeline |

---

**Related:** feed its query/path/explain results into an [init-harness](../init-harness/) Goal Packet's `inputs`; complements [token-efficiency](../token-efficiency/)'s read-only discipline. See the [root README](../../README.md) for how the skills interlock and navigate.
