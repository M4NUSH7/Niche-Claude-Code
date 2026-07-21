# Optional exports and the MCP server (adapted from graphify's
# references/exports.md, commit c83085c)

Read this only if the project wants a graph export in another tool, or a
live MCP tool path instead of one-shot CLI calls. None of this is required
for the query/path/explain navigation workflow in SKILL.md.

## Export formats

```bash
graphify export svg              # graphify-out/graph.svg (embeds in Notion, GitHub)
graphify export graphml          # graphify-out/graph.graphml (Gephi, yEd)
graphify export neo4j            # graphify-out/cypher.txt, manual import
graphify export neo4j --push bolt://localhost:7687 --user neo4j --password PASSWORD
graphify export falkordb          # cypher.txt (OpenCypher) for FalkorDB
graphify export falkordb --push falkordb://localhost:6379
graphify export callflow-html     # Mermaid-based architecture/call-flow HTML
```

Neo4j/FalkorDB pushes use MERGE - safe to re-run without creating
duplicates. Default Neo4j URI is `bolt://localhost:7687` / user `neo4j`;
default FalkorDB URI is `falkordb://localhost:6379`, target graph
`graphify`, auth optional.

## graphify-mcp: optional live-tool path

`graphify-mcp` (installed alongside `graphify` by the same `uv tool install
graphifyy`) serves a graph over MCP instead of one-shot CLI calls, so
another agent or orchestrator can query it live as a tool:

```bash
python -m graphify.serve graphify-out/graph.json
# or, if graphify-mcp is on PATH:
graphify-mcp --graph graphify-out/graph.json
```

Exposes `query_graph`, `get_node`, `get_neighbors`, `get_community`,
`god_nodes`, `graph_stats`, `shortest_path` as MCP tools. Transport defaults
to stdio; `--transport http --host --port --api-key` are available for a
long-lived HTTP server.

This is documented here as an available path - it is not wired into this
skill. If a project wants a persistent MCP registration, register it the
same way any other MCP server is registered for the assistant in use (e.g.
add a `mcpServers` entry pointing `command` at the absolute interpreter
path and `args` at `["-m", "graphify.serve", "/absolute/path/to/graph.json"]`);
do this by hand rather than via `graphify install` (see SKILL.md's warning).

## Benchmark

```bash
graphify benchmark [graph.json]
```

Measures token reduction of querying the graph vs reading the raw corpus.
Useful once, on a corpus over ~5000 words, to show the win is real on this
particular repo.
