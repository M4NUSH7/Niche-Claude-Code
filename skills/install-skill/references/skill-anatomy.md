# Skill anatomy and formatting standards

## Layout

```
skill-name/
+-- SKILL.md          required - YAML frontmatter + workflow
+-- references/       docs loaded as needed (progressive disclosure)
+-- scripts/          executables (shell, python, SQL)
+-- templates/        user-installable extras (agent defs, config snippets, file templates)
+-- modules/          complete companion skills nested under this one (see below)
+-- bin/              binaries (CLI-target skills only)
+-- assets/           files used in output (fonts, images, boilerplate)
```

## Frontmatter

```yaml
---
name: skill-name            # IS the slash command (/skill-name) - kebab-case, short
description: "..."          # the ONLY triggering mechanism - see below
allowed-tools: Read, Grep, Glob, Bash    # OPTIONAL - restricts this skill's tool surface
---
```

Only `name` and `description` load at session start (the always-in-context metadata). The body loads on trigger; references load on demand. Write the description pushy and trigger-rich: what the skill does AND every phrase a user might say ("Use whenever the user mentions 'X', 'Y', 'Z', or asks to..."). Claude under-triggers skills by default - err toward more trigger phrases. Scope it away from sibling skills explicitly ("Not for X - the Y skill covers that").

### allowed-tools (give the skill exactly the tools it needs)

`allowed-tools` is an optional comma-separated whitelist of the tools an agent running this skill may call. Omit it and the skill inherits the full tool surface; set it and everything outside the list is unavailable for that skill's turn.

Set it when the skill's workflow calls a known, small set of tools - a read-only auditor needs `Read, Grep, Glob`, not `Write` or `Bash`. A tighter surface means the agent spends fewer tokens deciding among irrelevant tools and cannot wander into actions the skill never intended, which keeps output focused without degrading quality. The heuristic: list only the tools the documented steps actually invoke; when unsure whether a tool is needed, leave it off and add it back if a step fails for lack of it. A skill that legitimately needs everything (a full build/install flow) simply omits the field.

## Always-on skills (read-whole via a CLAUDE.md snippet)

Most skills load on trigger - the right default. But a few carry rules that must govern *every* turn, not just when a keyword fires (routing policy, an output contract, always-on token discipline). Skills do not auto-load their whole body; the honest mechanism for "always in effect" is a small snippet the user appends to `~/.claude/CLAUDE.md` (project or global), while the full skill body still loads on trigger for the detail.

When a skill needs this, ship a CLAUDE-md snippet under its own templates/ dir (~100 tokens: the load-bearing rules only) and have SKILL.md instruct the user to append it. Do not invent a "read-whole" frontmatter flag - there is none; the CLAUDE.md snippet is the real always-loaded surface. `token-efficiency` is the canonical example (its routing + concise-output rules must apply every turn, so it ships and installs a snippet).

## Progressive disclosure

SKILL.md stays under ~500 lines (ideally ~100): workflow + rule summaries + pointers. Detail lives in references/, each pointer stating WHEN to read it ("Read before Step 4", "consult per-command, don't read whole"). Large references (>300 lines) get a table of contents. Explain WHY rules exist - smart models follow reasoning better than bare MUSTs.

## modules/ pattern (bundling companion skills)

Complete skills can nest under an umbrella skill in `modules/<name>/` - each keeps its own SKILL.md and files. Critical caveat: nested skills DO NOT auto-trigger; only the parent's description is visible. The parent SKILL.md must route: list each module with when-to-read guidance ("when step X applies, read modules/foo/SKILL.md and follow it as if invoked"). Use when a set of skills serves one purpose and should install as one unit.

## templates/ pattern

Anything the USER installs elsewhere (agent definitions for .claude/agents/, CLAUDE.md snippets, project file templates) goes in templates/ - the skill instructs, the user copies. Skills cannot write to protected locations themselves.

## Content standards

- ASCII-only unless the user opts out: replace emojis and decorative unicode ([OK], [FAIL], WARNING:, ->, box-drawing to +|-).
- English throughout (multi-language repo docs: take the English version only).
- Imperative voice; examples over abstractions; output formats shown as exact templates.
- Version-sensitive facts (model IDs, tool availability) verified by search at build time, not assumed.
