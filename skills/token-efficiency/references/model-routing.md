# Model Routing (hard rules)

Route work to the cheapest model that does the job well. Pinned versions are deliberate: they are stable, well-characterized, and cheaper than latest. "Latest" is used only where specified below or when the user explicitly asks for it.

## Routing table

| Role | Model | ID | Overridable? |
|---|---|---|---|
| Master Orchestrator (primary chat) | Opus latest | (user's /model setting) | Yes - user setting |
| Coding Subagent Orchestrator | Opus 4.6 pinned | `claude-opus-4-6` | Only if user explicitly names a model |
| Coding Agents (repetitive codegen subagents) | Sonnet 4.6 pinned | `claude-sonnet-4-6` | Only if user explicitly names a model |
| Logging and comments | Haiku 4.5 | `claude-haiku-4-5` | Only if user explicitly names a model |

These are cost-tier choices, not "latest" - verify each ID is still Active before a project bumps it.

## Role definitions

- **Master Orchestrator** - the primary chat session. Defaults to Opus latest. It does not do repetitive work itself; it routes tasks to the roles below. A skill cannot switch the chat model - if the session is not on Opus latest, note it once and continue.
- **Coding Subagent Orchestrator** - a subagent that plans, decomposes, and reviews the work of coding agents. Spawn with `claude-opus-4-6`, NOT opus latest.
- **Coding Agents** - subagents doing repetitive, instruction-driven code generation (the orchestrator or user supplies the spec). Spawn with `claude-sonnet-4-6`, NOT sonnet latest.
- **Logging/comments** - writing log entries, changelogs, SQL log rows, md compile summaries, code comments. Always `claude-haiku-4-5`. Never burn Sonnet/Opus tokens on log prose.

## Enforcement

> **CORRECTED 2026-07-17.** This list used to read *"pass the model explicitly per the table."* That
> instruction **defeats the pin** and is why it is wrong: the Agent tool's `model:` takes a **tier
> alias** (`sonnet`/`opus`/`haiku`), not a model ID. Passing it resolves to *latest of that tier* and
> silently overrides the pinned ID in the agent's frontmatter - the exact "NOT latest" this file
> exists to prevent. Measured, not theorised:
>
> | Spawn | Runs as |
> |---|---|
> | `subagent_type: coder`, **no `model:`** | **`claude-sonnet-4-6`** - the frontmatter pin [OK] |
> | `subagent_type: coder`, `model: "sonnet"` | `claude-sonnet-5` - pin overridden [WARN] |

1. **Pin in the agent definition's frontmatter** (`model: claude-sonnet-4-6`) and spawn with
   **NO `model:` argument.** The frontmatter pin binds; the tier alias overrides it.
2. **Pass `model:` only for ad-hoc agents** (`general-purpose`, `Explore`) that carry no frontmatter
   pin. There the tier alias is the only lever, and latest-of-tier is the honest expectation.
3. Prebuilt agent definitions with pinned models are in `templates/agents/` (coder.md,
   orchestrator.md, logger.md) - copy to `.claude/agents/` in any project.
4. The user saying "use the latest model" or naming a specific model overrides the table for that
   task only.
5. **Verify by probe, not by config-reading.** Config, `settings.json`, and frontmatter agreeing is
   not proof - none of them is the runtime. Spawn with no `model:`, ask the agent to name its model,
   assert it matches the pin. That two-second check is the only thing that would have caught this.

## Effort

**Default `high`. Never `max`.** `max` is a deliberate per-task escalation the user asks for, never a
default. A harness that ships `max` burns reasoning budget on mechanical work forever, and does it
silently - nothing errors, the bill just grows. Agents never self-escalate above the project's ceiling
(a harness may define this ceiling as a `maxEffort` config key, e.g. init-harness's
`harness.config.json`; this skill has no config file of its own, so treat `high` as the ceiling unless
the user explicitly raises it for a task).

## Session pattern (adapted from the merged strategy docs)

Understand once with the expensive model, implement repeatedly with the cheap one:

1. Architecture/comprehension pass: orchestrator level (Opus).
2. All implementation, debugging, tests: coding agents (Sonnet 4.6).
3. All log/comment writing: Haiku 4.5.

Where the original strategies.md says "Opus for learning, Sonnet for development", read it through this table: those roles map to Coding Subagent Orchestrator and Coding Agents respectively, at their pinned versions.
