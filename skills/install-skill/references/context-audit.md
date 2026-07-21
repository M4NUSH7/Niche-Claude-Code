# Context audit and pruning (density gate)

A skill's context cost is not its disk size - it is what gets loaded, when, how often. Optimize the loading profile, not the byte count.

## The cost model (what actually pollutes context)

| Tier | Loaded | Cost profile |
|---|---|---|
| description (frontmatter) | EVERY session, always | permanent - the most expensive real estate that exists |
| SKILL.md body | every trigger | recurring - pay on each use |
| references/ | only when routed to | conditional - near-free if routing is precise |
| scripts/, bin/, assets/, templates/ | never (executed/copied, not read) | zero context cost regardless of size |
| orphans (nothing routes to them) | shouldn't load, but agents wander | risk + duplication cost |

Consequences: a 434-line test script costs nothing; 30 duplicated lines in SKILL.md cost on every single trigger, forever. Prune by tier, not by size.

## THE HARD CONSTRAINT

Never rewrite, paraphrase, summarize, or "tighten" skill content during packaging or optimization - unless the user explicitly asks for a content rewrite. Allowed operations preserve content exactly:

1. **DELETE** files that carry no unique skill content (see prune list).
2. **MOVE** content verbatim between files (cut-paste whole blocks; hot->cold demotion).
3. **ADD** navigation only: when-to-read pointers, tables of contents for references >300 lines.

Quality lives in the content; density comes from placement. If density seems to require rewriting, the answer is moving to a colder tier, not compressing the words.

## Prune list (safe deletes - confirm via MCQ, recommended ON)

- Upstream repo meta: CONTRIBUTING, CHANGELOG, SECURITY, CODE_OF_CONDUCT, release configs, CI files, .github/.cursor/.opencode/.qwen dirs.
- Non-English documentation variants (README_fr.md etc.).
- Empty placeholders: evals/ dirs containing only .gitkeep, empty folders.
- True orphans: files with no inbound pointer from SKILL.md or any reference AND whose content already exists elsewhere in the package.
- Keep even though never loaded: LICENSE (legal), scripts and their tests (zero context cost, needed for function), binaries.

## Duplicate consolidation (move, don't rewrite)

When the same content exists in two places (common after merging sources): keep ONE canonical location, delete the other copy, fix all pointers to the canonical one. Choosing which copy survives is a placement decision, not a rewrite. If two files overlap partially, move the unique parts verbatim into the canonical file, then delete the husk.

## Hot/cold placement

- SKILL.md carries ONLY what every invocation needs: workflow, rule summaries, routing pointers. Anything situational (install guides, per-command references, troubleshooting) demotes verbatim to references/ with a when-to-read pointer.
- References used rarely but large get a TOC plus instruction to grep/offset-read sections, never read whole.
- The description is authored, not acquired - keep it trigger-rich but avoid restating body content (only place where every token is paid on every session).

## Audit procedure

Run `scripts/verify_skill.py <dir> --audit`. It reports: per-tier token estimates, permanent + per-trigger cost, orphan files, cross-file duplicate paragraphs, oversized references lacking a TOC, and prune candidates by the list above. Every reported item becomes an MCQ decision (delete / demote / keep) with a recommendation - deletions are never silent. Re-run after pruning: orphans zero, duplicates zero, per-trigger cost at or below pre-prune, content byte-count of surviving skill text unchanged except deletions the user approved.
