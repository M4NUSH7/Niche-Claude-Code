# Navigating a built graph: query, path, explain (adapted from graphify's
# skills/*/references/query.md, commit c83085c)

Read this when you are about to run `graphify query`, `graphify path`, or
`graphify explain` and want the full semantics - traversal modes, the
vocabulary-expansion trick for off-vocabulary questions, and the optional
work-memory loop. For the bare command syntax, SKILL.md is enough; come here
for *why* a query returned nothing, or how to phrase one better.

All three commands read `graphify-out/graph.json` (or `--graph <path>`) and
never touch your source files again once the graph exists.

## query: two traversal modes

| Mode | Flag | Best for |
|------|------|----------|
| BFS (default) | _(none)_ | "What is X connected to?" - broad context, nearest neighbors first |
| DFS | `--dfs` | "How does X reach Y?" - trace a specific chain or dependency path |

```bash
graphify query "how does authentication work"
graphify query "how does authentication work" --dfs --budget 3000
```

`--budget N` caps the output at N tokens (default 2000) - raise it if the
answer got truncated and you need more of the subgraph.

## Why a query can return zero hits

`graphify query` matches node labels via case-folded substring + IDF - there
is no stemming, no synonyms, no cross-language matching. If your question
uses different words than the graph's labels (you say "auth", the graph's
labels say "Guardian"; you ask in a language the code wasn't written in),
the literal matcher can return nothing and the answer collapses to noise.

Fix this by expanding your query against the graph's own vocabulary before
you ask, instead of guessing synonyms from training memory:

```bash
python -c "
import json, re
from pathlib import Path
data = json.loads(Path('graphify-out/graph.json').read_text(encoding='utf-8'))
vocab = set()
for n in data['nodes']:
    for c in re.findall(r'[^\W\d_]+', n.get('label','') or '', re.UNICODE):
        parts = re.findall(r'[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+', c) or [c]
        for p in parts:
            t = p.lower()
            if 3 <= len(t) <= 30:
                vocab.add(t)
print('\n'.join(sorted(vocab)))
"
```

Pick up to ~12 tokens from that exact vocabulary list that match your
question's intent - never invent a token that is not in the list. If
nothing in the vocabulary plausibly matches, say so; the corpus has no
relevant content for that question, and running the query anyway just
produces noise. Join the selected tokens with spaces and use that as the
query string instead of your original phrasing.

## path: shortest route between two concepts

```bash
graphify path "AuthModule" "Database"
```

Prints each hop with its relation and confidence tag, e.g.:

```
Shortest path (3 hops):
  FastAPI --uses--> DefaultPlaceholder <--references-- get_request_handler() --references--> ModelField
```

Explain the path in plain language afterward - what each hop means and why
it matters - rather than just pasting the raw hop list.

## explain: everything connected to one node

```bash
graphify explain "APIRouter"
```

Returns the node (source file, community, degree) plus every neighbor, the
relation, and the confidence tag:

```
Node: APIRouter
  Source:    routing.py L2210
  Community: 2
  Degree:    47

Connections (47):
  --> RequestValidationError [uses] [INFERRED]
  --> Dependant [uses] [INFERRED]
  --> .get() [method] [EXTRACTED]
  <-- __init__.py [imports] [EXTRACTED]
  ...
```

Write a 3-5 sentence explanation from this: what the node is, what it
connects to, and why those connections matter. Cite `source_location` when
quoting a specific fact - never invent an edge that is not in the output.

## Optional: closing the feedback loop (save-result / reflect)

After answering from `query`/`path`/`explain`, you can save the Q&A back so
future sessions reuse it instead of re-deriving:

```bash
graphify save-result --question "how does authentication work" \
  --answer "<your answer text>" --type query --nodes NODE1 NODE2 \
  --outcome useful   # or dead_end | corrected (pairs with --correction)
```

`graphify reflect` aggregates everything under `graphify-out/memory/` into
`graphify-out/reflections/LESSONS.md` - preferred sources, known dead ends,
and past corrections. This is optional bookkeeping, not required for basic
navigation; skip it unless the project wants a persistent memory layer.

## Honesty rule

Answer using only what the graph subgraph actually contains. If the graph
lacks enough information, say so - do not hallucinate an edge or a
relationship that isn't in `graph.json`.
