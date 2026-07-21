# Append this block to ~/.claude/CLAUDE.md (global) or project CLAUDE.md.
# It keeps routing + output rules ALWAYS in context (~100 tokens); the
# token-efficiency skill carries the full detail and loads on trigger.

## Token efficiency (always on)

- Model routing: coding subagents = claude-sonnet-4-6; coding orchestrator subagent = claude-opus-4-6; logs/comments = claude-haiku-4-5. Never "latest" for subagents unless I name a model.
- Prefix shell commands with `rtk` when installed (`rtk gain` to verify).
- Grep `[SOT:` tags and the README SoT index before exploring code; query .agents/memory.db before re-planning (failures: SELECT learnings FROM agent_compile_logs WHERE status='FAILURE').
- Concise output: answer directly, lead with the outcome, minimum words. No action narration (no "Let me.../Now I'll...") - the tool-call log already shows what ran; text is only for findings, decisions, caveats, and what I must do. No recap of what a command just printed; no status theater ("done", "all passes"); update memory silently. Announce actions as {tool {optimized args}}; cite code as file:line. Never cut error diagnoses, correctness caveats, requested reasoning, or code. "verbose" lifts this.

<!-- token-efficiency:learn:start -->
<!-- Regenerated at checkpoint time - do not hand-edit between these markers, see references/memory-system.md -->
<!-- token-efficiency:learn:end -->
