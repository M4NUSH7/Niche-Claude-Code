# ponytail

**Forces the laziest solution that actually works - simplest, shortest, most minimal.**

## What it does

Channels a senior dev who has seen everything and reaches for less: question whether the task needs to exist at all (YAGNI), standard library before custom code, native platform features before dependencies, one line before fifty. Supports intensity levels `lite`, `full` (default), `ultra`.

It is prose-first (the laziness ladder is judgment, not something to mechanize), but ships mechanical teeth for the two checkable rules:

- `scripts/harvest_debt.py` - greps `ponytail:` deferral comments into a debt ledger so deliberate shortcuts get tracked instead of rotting into "later means never". (Excludes backtick/heading examples so it does not match documentation of the marker.)
- `scripts/check_left_behind.py` - asserts a non-trivial change left at least one runnable check behind.
- `scripts/check.sh` - wraps `lizard` as the one cross-language complexity/length/param + duplication spine check.

It consolidates six previously-fragmented skills into one, with subcommands:

| Command | Trigger | Does |
|---|---|---|
| `/ponytail` | "be lazy", "simplest solution", "yagni" | The ladder, on any coding task |
| `/ponytail-review` | "review for over-engineering", "what can we delete" | Diff review, deletion-focused |
| `/ponytail-audit` | "audit this codebase", "find bloat" | Whole-repo over-engineering scan |
| `/ponytail-debt` | "what did ponytail defer", "ponytail ledger" | Harvest `ponytail:` markers |
| `/ponytail-gain` | "what does ponytail save" | Benchmark scoreboard |
| `/ponytail-help` | "ponytail help" | Reference card |

## Why it works

Over-engineering is the default failure mode of capable code models - they add abstractions, flags, and defensive handling for cases that cannot happen. ponytail is a persistent counterweight applied *before* the first line, plus a debt ledger so the corners it deliberately cuts stay visible and payable. The one bundled tool (`lizard`) turns three prose rules (complexity, function length, param count) into one runnable cross-language check.

## How to use

Say "ponytail", "be lazy", "simplest solution", "minimal", "yagni", "do less", or complain about bloat/boilerplate/over-engineering. It applies to writing, adding, refactoring, fixing, reviewing, or designing code and choosing dependencies. Not for non-coding requests.

## Key files

| Path | Purpose |
|---|---|
| `SKILL.md` | The ladder + rules (the prose core) |
| `commands/*.md` | The six consolidated subcommands |
| `scripts/harvest_debt.py` | `ponytail:` marker -> debt ledger |
| `scripts/check_left_behind.py` | Assert a runnable check was left behind |
| `scripts/check.sh` | `lizard` spine check (complexity/length/params/dupes) |
