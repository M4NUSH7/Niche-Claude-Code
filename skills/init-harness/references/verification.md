# Verification - why "the files exist" proves nothing

## The failure this catches

A harness can have a perfect tree, valid config, correctly-wired hooks in `settings.json`, and
**enforce nothing.**

That is not hypothetical - it is what the original template shipped. It pinned `py -3` for every
hook command. On a machine with no `py` launcher:

```
$ py -3 .claude/hooks/big_read_guard.py
py: command not found
exit=127
```

The hook process never starts. So it doesn't fail *open* - it fails **absent**:

| | fails open | fails **absent** |
|---|---|---|
| Guard runs? | yes | **no** |
| Logs a fail-open row? | yes | **no** |
| Detectable? | yes - `harness_status.py` counts them | **no. Nothing anywhere.** |

An existence check passes this harness with full marks. `sync_harness.py --check` says OK. The
tree is flawless. And every read guard, gate guard, and audit log is decorative.

**So: verify behaviour.** Every check in `verify_init.py` asserts an *action*.

## What it proves

| # | Check | Asserts | Catches |
|---|---|---|---|
| 0 | interpreter executes | exit 0 | the absent-hook failure - everything below is meaningless if this fails |
| 1 | read guard blocks unbounded read | **exit 1** | audit #5, and a dead interpreter |
| 1 | read guard blocks `limit > maxLines` | **exit 1** | the audit #5 bypass specifically |
| 1 | read guard allows windowed read | exit 0 | over-blocking (a guard that blocks everything gets disabled) |
| 2 | at least one terminal has `neverBlocked:true` | present | a topology where every terminal can deadlock on a gate |
| 2 | gated terminal blocked while tag missing | **exit 1** | audit #2 - gates as mechanism, not prose |
| 2 | cross-domain write blocked | **exit 1** | domain boundaries |
| 2 | (no gated/cross-domain case exists) | **FAILS LOUD**, not a silent SKIP | a degenerate/single-terminal topology where the gate mechanism was never exercised |
| 3 | PostToolUse writes a JSONL row | file exists | audit #8 - a logger that stops logging |
| 4 | `sync --check` OK | exit 0 | audit #1 drift **and orphans** |
| 5 | `status --check` OK | exit 0 | checkbox <-> tag <-> disk reconciliation |
| 6 | pivot template + human gate | present | the pivot mechanism is installed |
| 7 | agent frontmatter `model:` == config-resolved ID | static equality | drift between the stamped pin and the config - necessary but NOT sufficient; see the printed runtime-verification steps (spawn with no `model:`, check `/debug`, never trust self-report) |
| 8 | every stamped effort is in the valid enum and `<= maxEffort` | valid + bounded | A1 - an invalid or self-escalated effort value |
| 9 | network reachability to a configurable host:port | **report only, never hard-fails** | "report the gap, don't design around it" - environment connectivity is a fact, not a harness defect |
| 10 | `.agents/memory.db` exists and `agent_compile_logs` is queryable | **report if absent, hard-fail if present-but-broken** | D1 - the FAILURE-recall table being silently unqueryable when the DB *is* there |

## Read the audit trail before believing a failure

During this harness's own rebuild, a test appeared to prove the read guard was broken - it
allowed `limit: 9999`. The guard's own log said otherwise:

```json
{"action": "fail-open", "error": "stdin parse: Expecting value: line 1 column 1 (char 0)"}
```

The **test harness** wasn't delivering stdin. The guard was fine. Re-run correctly, all four cases
passed.

Two lessons worth keeping:
1. **Fail-open logging paid for itself.** It's the only thing that makes a silent hole findable  - 
   and here it caught a *tester's* error, not the guard's.
2. **Check `{tree}/logs/hooks.jsonl` before declaring a guard broken.** If you see `fail-open` with
   a stdin parse error, your test is wrong, not the hook.

## Gate revocation - the pivot claim, proven

"Revoking a tag re-blocks dependents" is a claim, so prove it:

```bash
export HARNESS_TERMINAL=t2                       # t2 blockedUntil: [scaffold-complete]
W='{"tool_input":{"file_path":"apps/domain-a/x.ts"}}'
echo "$W" | <py> .claude/hooks/gate_guard.py     # exit 1 - no tag, blocked
git tag scaffold-complete
echo "$W" | <py> .claude/hooks/gate_guard.py     # exit 0 - gate open
git tag -d scaffold-complete                     # pivot revokes it
echo "$W" | <py> .claude/hooks/gate_guard.py     # exit 1 - re-blocked
```

Block -> allow -> block, with **zero changes to `gate_guard.py`**: "does the tag exist?" was already
the right question.

## Rule

**If verification fails, stop.** Do not hand over a harness that doesn't block - the user will
build on it believing they're protected, and the first sign of trouble will be a 500-line read or
a cross-domain write that nobody logged.
