# Source-of-Truth (SoT) Keyword Framework

Agents waste tokens guessing file hierarchies and scanning blindly. Instead, standardized tokens are inserted into code comments and log headers, and agents grep for them BEFORE writing code. The map is cheap; the blind scan is not.

## Token grammar

```
[SOT:CATEGORY]              category marker
[SOT:CATEGORY:name]         named block within a category
[SOT:IDX:name]              one-off item, individually indexed (frequency < 5)
```

Rules: UPPERCASE categories, kebab-case names, always inside a comment for the host language (`// [SOT:AUTH:jwt-refresh]`, `# [SOT:DB:migrations]`, `<!-- [SOT:CONFIG:env] -->`). The bracket syntax never collides with real code and is trivially greppable and AST-parser friendly.

## Agent workflow (mandatory before writing code)

1. Read the SoT index in the project README (see below) - this is the category map.
2. Map exact locations with tool calls, never by browsing:
   ```bash
   rtk grep -rn "\[SOT:AUTH" --include=*.py     # all auth source-of-truth blocks
   rtk grep -rn "\[SOT:" src/ | head -50        # full map of a subtree
   ```
3. Only then read the specific blocks found, with offset/limit.

Never blind-scan a directory tree when an SoT grep can answer the question.

## The README index (required)

Every project using this framework has a keyword index in `README.md` (or `.agents/README.md` for projects that keep the root README user-facing). Template: `templates/sot-readme-template.md`. It lists every category, its meaning, its keywords, and where it is used (code, logs, or both). All keyword categorization lives in this one file - it is the map agents read first.

## Categories: seeding and promotion

- **At project init/setup:** seed default categories from the project goal (e.g. a web app seeds AUTH, DB, API, CONFIG, UI, TEST, BUILD, DEPLOY). Record them in the README index.
- **During work:** agents do repetitive work in loops; over time most work falls into definable categories. When an agent encounters something with no category:
  - If it looks recurring or reaches 5+ occurrences: define a new category, add it to the README index, tag occurrences with `[SOT:NEWCAT:...]`.
  - If it is a one-off (< 5 total frequency): tag as `[SOT:IDX:name]` and list it individually in the index. Do not create single-use categories.
- **At checkpoint:** review `[SOT:IDX:*]` entries; any that reached 5+ get promoted to a real category and re-tagged.

**OPTIONAL tier - flat categories are the load-bearing part.** The flat category enum, the one-per-file
SoT header, and the README index (above) are what actually pays off day to day - keep those unconditionally.
The `[SOT:IDX:name]` one-off tier and its mirror in the `sot_keywords` SQLite table (see
`memory-system.md`) are populated only by hand ritual today: an agent is *told* to insert/update rows,
but no hook enforces it, so the table silently drifts from the code the moment someone forgets the step.
Treat `IDX:`/`sot_keywords` as deprecated-by-default. Only keep populating it if it becomes a byproduct of
an existing mechanical write (e.g. the logger's `INSERT OR IGNORE` + `frequency+1` described in
`memory-system.md`) rather than a separate manual step - otherwise skip it and rely on the flat categories
and README index alone.

## Logs

Same keywords, same index. Log files live under `{agent-name}/logs/` (or as rows in the SQLite memory - see memory-system.md, which is preferred for anything beyond trivial size). Every log entry starts with its SoT tags so recall is a grep or a WHERE clause, not a read-everything pass.
