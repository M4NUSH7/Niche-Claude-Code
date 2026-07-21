# Permissions and rules - ask, never assume

**Never silently choose a permission posture for someone.** The original kit shipped
`"allow": ["Bash(*)"]` with `"deny": []` - unrestricted shell, never asked about. That is root
access with extra steps, presented as a default. Every permission decision in this skill is an
**MCQ with a recommendation**.

## Precedence (get this right or the rest is theatre)

```
deny  >  ask  >  allow
```

`deny` is absolute - nothing overrides it, no profile widens it. So the deny list is where the
real safety lives; `allow` only decides how often you get prompted.

## Q1 - Permission profile (ask always)

> **How much autonomy should agents have in this repo?**

| Option | Behaviour | Pick when |
|---|---|---|
| **Balanced (Recommended)** | Read/grep/edit free; safe git + file commands free; network, installers, destructive git **ask**; secrets + history-rewrites **denied** | Almost always. The hooks are the real enforcement. |
| Strict | Every write and every shell command asks | Production repo, unfamiliar codebase, or you want to watch every move |
| Permissive | Most Bash allowed; only the deny list blocks | Throwaway/sandbox repo you could delete without caring |
| Custom | You hand-author allow/ask/deny | You have a house policy. sync won't overwrite it. |

**Why Balanced is the recommendation:** this harness enforces discipline *mechanically* - the read
guard blocks oversized reads, the gate guard blocks premature and cross-domain writes, every tool
call is logged. Permission prompts are the outer, weaker ring. Making a human confirm 200 `ls`
calls trains them to click "yes" without reading, which is how the *real* prompt gets approved by
reflex.

## Q2 - Network + installers (ask always)

> **Should agents reach the network and install packages without asking?**

| Option | Behaviour |
|---|---|
| **Ask each time (Recommended)** | `curl`, `gh`, `docker`, `npm/pnpm/pip/cargo/uv`, `scoop` prompt |
| Allow | No prompt - fastest, but an agent can install anything and phone anywhere |
| Deny | Blocked entirely - fully offline work |

**Recommended = ask.** Installs are the main supply-chain surface and the main way a "small fix"
silently adds a dependency. Tied to the toolchain rule: harness tools go **global** (scoop / `uv
python install`), never vendored in-project.

## Q3 - Git attribution (ask always; default is OFF)

> **Should Claude tag itself as a co-author on commits and PRs?**

| Option | Result |
|---|---|
| **No - no attribution (Recommended, DEFAULT)** | `attribution: {commit: "", pr: ""}` - no `Co-Authored-By` trailer, no PR line |
| Yes | Standard Claude Code attribution |
| Custom | Your own trailer text |

**Default is off**, per the project owner's instruction. `attribution` supersedes the deprecated
`includeCoAuthoredBy`. This is a config field - not something an agent should decide per commit.

## Q4 - Sensitive paths (ask; prefilled)

> **Confirm the paths that auto-escalate review and require the security checklist.**

Prefilled from the kit defaults, filtered to directories that exist. Credentials/keys, money
movement, identity/auth, admin surfaces. Every false positive escalates cost and trains people to
ignore escalations - keep it tight.

## The non-negotiable deny list

Re-stamped by `sync_harness.py` into **every** profile, including Permissive. These aren't
preferences:

| Rule | Why |
|---|---|
| `git push --force*`, `git push -f*` | Destroys others' work; unrecoverable remotely |
| `git reset --hard*`, `git clean -fdx*` | Destroys uncommitted work; no undo |
| **`git tag -d*`, `git push origin --delete*`** | **Gate revocation is a human-approved pivot action (principle #11).** An agent must never withdraw a gate. |
| `rm -rf /*`, `rm -rf ~*` | Obvious |
| `Read(**/.env)`, `*.pem`, `*.key`, `id_rsa*`, `.ssh/**` | Secrets leak into transcripts, logs, and the SQLite audit trail |
| `Edit/Write(.agents/**)` | Generated tree - hand-edits are silently overwritten and fail CI |

That `git tag -d` line is the interesting one: the pivot mechanism *requires* revocation, and this
denies it to agents. That's the point - **propose, don't act**.

## Agent rules (distinct from permissions)

Permissions are mechanical (the harness blocks you). Rules are behavioural (the prompt tells you).
Both are needed; neither substitutes for the other.

| Rule | Where it lives | Enforced by |
|---|---|---|
| Effort ceiling `high`; no self-escalation | config `maxEffort` + agent frontmatter | prompt only |
| Architect refuses low-effort tasks; coder refuses to re-architect | agent prompts | prompt only |
| Read the routed architecture doc before touching a layer | agent prompt + `docRouting` | prompt only |
| Stay in your domain | config `terminals[].paths` | **`gate_guard.py`** |
| Don't build before your gate opens | config `blockedUntil` | **`gate_guard.py`** |
| No unbounded reads | config `readGuard` | **`big_read_guard.py`** |
| Every tool call is logged | config `logging` | **`log_tool_use.py`** |
| Security checklist on sensitive paths | config `sensitivePaths` | prompt + review escalation |
| **Propose pivots; never declare work dead** | `11_pivots.md` + agent prompts | prompt **+ `git tag -d` deny** |
| Simplicity ladder before new code | `ponytail` skill | prompt only |

**The asymmetry is deliberate.** Anything catastrophic and irreversible is mechanical. Anything
that needs judgment is a prompt rule - because a mechanism that fires on judgment calls gets
disabled by the third false positive.

## Emit into CLAUDE.md

```markdown
## Rules
- Effort ceiling is HIGH. Never self-escalate; only the human raises effort.
- Stay in your terminal's domain. Cross-domain work is a handoff, not a write.
- Never build before your gate tag exists.
- Read the routed architecture doc before touching that layer.
- Sensitive paths: load the security checklist. Any failure = do not merge.
- PROPOSE pivots with evidence; never mark `- [~]`, revoke a gate, or delete built
  work on your own authority. A human approves. (setup/11_pivots.md)
- Simplicity ladder before writing anything new (ponytail).
```
