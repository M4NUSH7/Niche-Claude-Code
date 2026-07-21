# 01 - Core Principles (preserve these verbatim when reusing)

These are the conventions that make the harness work. Everything else is decoration.

## 1. One task pointer, on disk
Every terminal's current task is **the first unchecked checkbox** in its `.bld/tN/phases.md`.
Session start ritual: load `context/agents/tN-context.md`, open `.bld/tN/phases.md`, do the first
`- [ ]` item. No task tracker, no ambiguity, survives session resets for free.
Four states: `- [ ]` open . `- [x]` done . `- [~]` **superseded** (built, then pivoted away from -
see `11_pivots.md`) . `- [!]` **blocked/awaiting-human** (stuck on a decision only a human can
make, links a `memory/decisions/` note - see `06_memory_and_context.md`). The last two count as
neither progress nor queue.

## 2. Pinned model + effort per role, hard ceiling
Each named agent has a **pinned model and effort level** in settings (`architect`=opus/high,
`coder`=sonnet/high, `verifier`=sonnet/medium, `logger`=haiku/low, ...). Effort ceiling is
**High**; agents never self-escalate - only the human raises effort, temporarily, in main chat.
This is the cost-control backbone: the expensive model thinks, the cheap model types, the
cheapest model logs. A judgment call (e.g. deciding what's worth compressing into durable
`learnings`) is never silently downgraded to the logging pin just because it touches the same
logs the logger writes - see `references/decision-guide.md` Part V.3.

## 3. Skills lazy-load; one efficiency skill always on
Only `token-efficiency` auto-loads. Every other skill declares an explicit trigger
(`loadOn`) and is loaded by name ("Loading skill: X") when - and only when - the trigger fires.
Reference sub-files inside a skill load only when the skill's router points at them.
(Coursly measured ~15,000 tokens saved per session vs pre-loading.)

## 4. Memory lives in exactly one place
`memory/` is an Obsidian vault with `INDEX.md` as hub. **No flat memory files anywhere else.**
Decisions get a dated entry; navigation is wikilinks/backlinks. Docs may summarize memory but
never fork it.

## 5. Interactive vs autonomous configs are separate, logs never mix
`.claude/` serves interactive Claude Code; `.agents/` serves autonomous runners. Same agents,
same skills, **separate SQLite logs** (`.claude/logs/{agent}/{agent}.db` vs `.agents/logs/...`)
so output provenance is always traceable. (See `09_AUDIT.md` - keep the trees generated, not
hand-mirrored.)

## 6. Hooks enforce what prompts merely request
- **PreToolUse read guard**: any `Read` of a >500-line file without an explicit `limit` is
  blocked -> forces grep/head/offset. Token discipline as a mechanism, not a plea.
- **PostToolUse SQLite logger**: every tool use becomes a row in the acting agent's DB.
  Auditable with one `sqlite3` query.

## 7. Gates are the concurrency contract
Terminals run in parallel but cross-domain dependencies are **git-tag gates**
(e.g. nothing starts until T1 tags `scaffold-complete`; payments wait for the ledger; a security
pass is required before merging anything touching money/identity/admin). One terminal owns each
gate; the others' checklists state their unblock condition.

## 8. Simplicity doctrine with teeth ("ponytail")
A YAGNI ladder applied before any new code: build at all? -> already in codebase? -> stdlib? ->
platform feature? -> installed dep? -> one line? -> minimum that works. Deletion beats addition;
deliberate simplifications are marked with a `ponytail:` comment; non-trivial logic ships with one
runnable assert-based check. Reviewer and architect apply the same lens ("could this be deleted?").

## 9. Security is a gate, not a review
Sensitive paths (money, identity, admin) are enumerated up front. Touching them auto-escalates the
reviewer to the strong model and loads the security checklist skill. "If any item fails: do not
merge" - checklists, not vibes.

## 10. Docs are routed, not read wholesale
`architecture/` holds one decision doc per layer; the rule is "read the relevant doc before
touching that layer," and agent prompts route by topic (DB question -> doc 03, security -> doc 08).
`context/architecture/system-overview.md` is the 1-page quick reference.

## 11. Humans hold the promote button
The human gate list is explicit and short (approve plans, raise effort, approve gate merges,
**approve pivots**, pre-flight legal/business steps). Everything else is automated. The system
never self-promotes past a gate.

**Pivot approval is a human gate.** No agent may unilaterally declare built work dead. An agent
may *propose* a pivot - loudly, with evidence - but only a human approves one. The asymmetry is
deliberate: an agent wrongly continuing costs tokens; an agent wrongly deleting three weeks of
work costs three weeks. Full doctrine: `11_pivots.md`.

## 12. Reversal is a first-class operation
Forward progress is not the only direction. When work is abandoned or refactored away, the
harness records it rather than quietly forgetting: superseded tasks are marked `- [~]` with a
link to a pivot note, invalidated gate tags are **revoked and re-earned**, the narrative goes in
`memory/decisions/`, and the "don't retry this" warning goes in `agent_compile_logs` where agents
actually query it. A build that cannot express "we were wrong" accumulates false history - and
every agent downstream trusts it. See `11_pivots.md`.
