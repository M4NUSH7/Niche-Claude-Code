# How graphify works (distilled from docs/how-it-works.md, commit c83085c)

Read this to understand what `graphify update` actually did to produce
`graph.json`, and what the fields in that file mean. Not needed just to run
a query - see SKILL.md for the day-to-day commands.

## The three passes

graphify processes files in three passes:

**Pass 1 - Code structure (free, no API calls)**
Tree-sitter parses code files and extracts classes, functions, imports, call
graphs, and inline comments. This runs locally with no LLM involved, across
~40 languages. SQL files get special treatment: tables, views, foreign keys,
and JOIN relationships are extracted deterministically. This is the pass
`graphify update` uses - a code-only corpus never reaches passes 2 or 3.

**Pass 2 - Video and audio (local, no API calls)**
Video and audio files are transcribed with faster-whisper, seeded with the
top god nodes from the code graph so far to focus the transcript on-domain.
Transcripts are cached; re-runs skip already-processed files.

**Pass 3 - Docs, papers, images (LLM subagents, costs tokens)**
An LLM runs in parallel over markdown, PDFs, images, and transcripts. Each
subagent reads a batch of files and outputs a JSON fragment: nodes, edges,
and any group relationships, merged into the graph. This pass needs an LLM
(or a configured API key) - `graphify update` (the pure-CLI path this skill
uses) does not invoke it. It only applies to the full orchestrated skill
flow the upstream repo ships (not installed here - see SKILL.md's warning).

## How community detection works ("clustering")

Communities are found with the Leiden algorithm - a graph-clustering method
that groups nodes by edge density. Nodes with many connections between them
end up in the same community. No embeddings needed: the graph structure
itself is the similarity signal. This is what `--no-cluster` skips.

## Confidence tagging

Every relationship is tagged with one of three labels:

| Tag | Meaning |
|-----|---------|
| `EXTRACTED` | Found directly in the source (e.g. a function call, an import) |
| `INFERRED` | A reasonable inference, with a `confidence_score` (0.0-1.0) |
| `AMBIGUOUS` | Uncertain - flagged for manual review |

EXTRACTED edges always have confidence 1.0. INFERRED edges use a discrete
rubric: 0.95 near-certain, 0.85 strong evidence, 0.75 reasonable, 0.65 weak,
0.55 speculative.

## Token benchmark

The first `update` costs tokens (or nothing, for a pure-code corpus - AST
extraction is free). Every subsequent `query`/`path`/`explain` reads the
compact graph instead of raw files - that is where the savings compound. On
a mixed corpus (code + papers + images, 52 files), the upstream benchmark
measured 71.5x fewer tokens per query vs reading the raw files directly.
Token reduction scales with corpus size; a handful of files already fits in
context, so the value there is structural clarity, not compression.

## SHA256 cache

Every extracted file is fingerprinted by content hash. Re-runs (`graphify
update`) skip unchanged files entirely - only new or modified files go
through extraction again. The cache lives in `graphify-out/cache/`.

## The graph.json format

NetworkX node-link format. Each node has:
- `id` - stable identifier
- `label` - human-readable name
- `file_type` - `code`, `document`, `paper`, `image`, `rationale`
- `source_file` - where it came from

Each edge has:
- `source`, `target` - node IDs
- `relation` - verb phrase (e.g. `calls`, `imports`, `implements`, `semantically_similar_to`)
- `confidence` - `EXTRACTED`, `INFERRED`, or `AMBIGUOUS`
- `confidence_score` - float (INFERRED only)
- `source_file` - where the relationship was found

Hyperedges (group relationships connecting 3+ nodes) live in
`G.graph["hyperedges"]`.
