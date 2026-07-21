# Niche Claude Code Skills

A curated set of **Agent Skills** for Claude Code (and Cowork) that make an agent
cheaper, more disciplined, and better at large multi-step builds - without
losing output quality. Each skill is self-contained, verifiable, and installable
as a plain folder (Code) or a `.skill` upload (Cowork).

---

## Why this exists

Capable coding models share a set of predictable failure modes:

- **They narrate and re-read.** Tokens get burned on "Let me now..." narration and
  on re-injecting the same file context every turn.
- **They over-engineer.** Extra abstractions, flags, and defensive handling for
  cases that cannot happen.
- **They lose the plot on long builds.** A subagent claims "done" without a real
  check (inferred-done), retries silently forever (hallucination loops), or dies
  leaving no trace of why (lost failures).
- **They produce mundane, interchangeable UI** - the same three-column grid and
  Inter-on-white for every app.
- **They re-read the whole log pile** to "remember" what happened.

These skills each attack one of those, and they are designed to **interlock**: the
token discipline, the build harness, and the codebase-navigation and scaffolding
skills reinforce each other rather than sit in separate silos.

The one design principle behind all of them:

> **Make it mechanical, enforce it at the real boundary, and prove behaviour by
> running or rejecting - never by existence.** If a rule requires an agent to
> remember a ritual against the grain of how agents work, it will erode. If it is
> a hook, a generator step, a git tag, or a probe that fails when the mechanism is
> broken, it survives.

---

## Estimated savings

> **This is a transparent cost model, not a measured benchmark.** The numbers below
> are calculated from each mechanism's own documented reduction on a representative
> mid-size agentic coding session - not from a controlled A/B run. Your mileage
> varies with workload; the arithmetic is shown so you can adjust it to yours.

Four independent levers compound on a typical session:

| Lever | Skill | Reduction applied | Basis |
|---|---|---|---|
| Command-output compression | token-efficiency (RTK) | ~70% off command/log output | RTK's documented 60-90% range, midpoint |
| Fewer redundant file reads | token-efficiency + graphify | ~40% off file-read tokens | grep/graph-query before blind re-read |
| No narration / recaps | token-efficiency (output contract) | ~80% off pure narration output | narration is ~all removable |
| Model routing | token-efficiency | codegen -> Sonnet, logging -> Haiku | price tiers $5/$25 -> $3/$15 -> $1/$5 |

**Worked example** - a session that (baseline, all-Opus, verbose) would run ~325K
tokens at ~$2.92:

- Token volume drops to ~189K -> **~40% fewer tokens**.
- With routing on the reduced volume, cost drops to ~$1.22 -> **~55-60% lower cost**.

**What the end user can expect:** roughly **40% less context burned and ~55% lower
spend per session at equal or better output quality** - because the cuts are all
narration, redundant reads, and wrong-model overhead, never the code, the reasoning,
or the error diagnoses (those are explicitly protected). On top of the raw savings,
the build-discipline skills (enforced definition-of-done, bounded retries, scoped
handoffs) remove the *silent* waste - hallucination loops and re-work - that no
per-turn number captures. Assumptions are deliberately conservative (RTK at its
midpoint, reads at only 40% off, output work never compressed); heavier
command/log-bound workloads save more.

## The skills

| Skill | One line | Attacks |
|---|---|---|
| [token-efficiency](skills/token-efficiency/) | RTK output compression + model routing + concise-output contract | narration, re-reading, wrong-model cost |
| [init-harness](skills/init-harness/) | Parallel-terminal build harness with mechanical gates, goal packets, enforced definition-of-done | inferred-done, hallucination loops, lost failures |
| [install-skill](skills/install-skill/) | Build/install a COMPLETE skill package, verified, per surface | half-installed skills, silent drops |
| [skill-creator](skills/skill-creator/) | Author + eval + benchmark + optimize a skill's triggering | skills that under-trigger or do not generalize |
| [ponytail](skills/ponytail/) | Force the laziest solution that works; track deferred debt | over-engineering |
| [ui-standout](skills/ui-standout/) | 3-layer method to pick standout components per use-case | mundane, interchangeable UI |
| [production-grade-scaffold](skills/production-grade-scaffold/) | Archetype/stack/cloud scaffolding + minimum-bar checklists | ship-readiness, structure |
| [graphify](skills/graphify/) | Query a relational code-graph instead of blind grep+read | re-reading files to navigate |
| [scrapling](skills/scrapling/) | Scrape with anti-bot bypass, stealth, spiders | `web_fetch` fails / protected sites |
| [agent-reach](skills/agent-reach/) | Zero-config internet research router across platforms | single-engine research narrowness |

Each folder has its own `README.md` with what/why/how/install and a key-files table.

---

## How they interlock

These are not ten unrelated tools - they compose:

- **token-efficiency is the substrate.** Its model-routing rules and output
  contract are meant to govern *every* turn (installed as a ~100-token CLAUDE.md
  snippet). Every other skill's subagents inherit it.
- **init-harness is the orchestration layer** and defers to token-efficiency for
  routing/output rather than restating it. Its **Goal Packets** carry
  machine-checkable `success_criteria`, `scope_boundaries`, and scoped `inputs`,
  so a subagent takes only its slice and **works until a definition-of-done that is
  assigned in code** (`verify_goal_packet.py`), not self-reported. Its `inputs`
  can point at **graphify** queries instead of file dumps.
- **production-grade-scaffold** answers "what should the codebase look like",
  which is orthogonal to init-harness's "who builds it" - so init-harness's
  context-bootstrap hands off to the scaffold for greenfield apps, and the scaffold
  routes to **ui-standout** for the Presentation layer.
- **install-skill + skill-creator** are the two halves of getting a new skill
  built and shipped: skill-creator authors and measures, install-skill packages,
  verifies, and installs. (This repo was packaged and verified with install-skill.)
- **ponytail, graphify, scrapling, agent-reach** are point tools any of the above
  can reach for - laziness enforcement, code navigation, scraping, and research.

The result is a stack where the cheap-but-good defaults (token discipline), the
build discipline (gates + goal packets + enforced DoD), and the point capabilities
(nav, scrape, research, scaffold, UI) all pull in the same direction.

---

## Installing

There are two surfaces, and they install differently. **Claude Code** (the CLI and
the desktop app's Code tab) and **Cowork** both run bundled scripts and binaries;
only plain claude.ai chat is script-limited.

### Claude Code (CLI + desktop Code tab)

Skills install as **plain folders** under `~/.claude/skills/`. Copy the folders you
want:

```bash
# macOS / Linux
cp -r skills/token-efficiency ~/.claude/skills/
cp -r skills/init-harness     ~/.claude/skills/
# ... etc for each skill you want
```

```powershell
# Windows (mirror-copy a single skill folder; never /MIR the shared parent)
robocopy "skills\token-efficiency" "$env:USERPROFILE\.claude\skills\token-efficiency" /MIR
```

For **token-efficiency**, also append its `templates/CLAUDE-md-snippet.md` block to
`~/.claude/CLAUDE.md` so the routing + output rules stay in context every turn (the
skill body loads on trigger; the snippet is the always-on part).

### Cowork

Cowork loads skills **enabled on your claude.ai account**, not from `~/.claude`.
Upload the `.skill` files in [`skills/cowork/`](skills/cowork/) via the Desktop app:
**Customize -> Skills -> upload**. The `-cowork` editions are adapted for Cowork's
Linux sandbox (e.g. token-efficiency-cowork bundles a **Linux** rtk binary; the CLI
edition bundles the Windows `rtk.exe`).

### Dependencies

Some skills wrap external tools (all cross-platform, installed on first use):

| Skill | Tool | Install |
|---|---|---|
| token-efficiency | RTK | bundled binary; else `curl -fsSL <rtk install.sh> \| sh` |
| ponytail | lizard | `pip install lizard` (optional, for the spine check) |
| graphify | graphify | `uv tool install graphifyy` |
| scrapling | Scrapling | `uv tool install "scrapling[all]"` then `scrapling install` |
| agent-reach | yt-dlp / gh / feedparser / mcporter | per channel, on first use |

---

## Repo layout

```
skills/
  <10 skill folders>          # the source - install these for Claude Code
    <skill>/SKILL.md          # the skill definition
    <skill>/README.md         # what/why/how for that skill
    <skill>/{references,scripts,templates,bin,...}/
  cowork/
    <10 .skill zips>          # the upload artifacts for Cowork / claude.ai
```

Only the `skills/` tree is published here - no local config, no scratch files.

---

## About

These skills were built and refined while running Claude Code across real
production codebases, then personalized for token efficiency and long-build
discipline - keeping the output quality while cutting the cost and the drift.
Nothing here is theoretical: each rule exists because a real build hit the
failure mode it prevents.

## Credits & upstream

Several skills are original to this repo; several are **repackaged from excellent
upstream projects** - adapted for Claude Code / Cowork, verified, ASCII-folded,
and with vendor installers deliberately **not** run (so they do not fight a
harness that owns `~/.claude`). Full credit and thanks to the authors:

| Skill / component | Upstream | License |
|---|---|---|
| **skill-creator** | [anthropics/skills](https://github.com/anthropics/skills) - Anthropic's official skill-authoring skill | Anthropic (see repo) |
| **scrapling** | [D4Vinci/Scrapling](https://github.com/D4Vinci/Scrapling) - the library author's own agent-skill, by Karim Shoair | BSD-3-Clause |
| **graphify** | [Graphify-Labs/graphify](https://github.com/Graphify-Labs/graphify) - the `graphifyy` code-graph CLI | MIT |
| **agent-reach** | [Panniantong/Agent-Reach](https://github.com/Panniantong/Agent-Reach) - English variant | MIT |
| **token-efficiency** -> RTK | [rtk-ai/rtk](https://github.com/rtk-ai/rtk) - the bundled Rust Token Killer binary | Apache-2.0 |
| **ponytail** -> lizard | [terryyin/lizard](https://github.com/terryyin/lizard) - the cross-language complexity spine check | MIT |
| **ui-standout** -> taste gate | [pbakaus/impeccable](https://github.com/pbakaus/impeccable) - the 46 anti-slop rules were harvested from here | Apache-2.0 |
| **ui-standout** -> principles | [Owl-Listener/designer-skills](https://github.com/Owl-Listener/designer-skills) - the design-principle references | MIT |
| **ui-standout** -> catalogs | [shadcn/ui](https://github.com/shadcn-ui/ui) (MIT), [StyleX](https://github.com/facebook/stylex) (MIT), [astryx](https://astryx.atmeta.com) (Meta), [Aceternity UI](https://ui.aceternity.com) - referenced as queryable component sources | see each |

**token-efficiency**, **init-harness**, **install-skill**, **ponytail**,
**ui-standout**, and **production-grade-scaffold** are authored/assembled here;
where they wrap or harvest an upstream (RTK, lizard, impeccable, designer-skills),
that upstream is credited above and in the skill's own `README.md` / `SKILL.md`.

If you own one of these upstreams and want the attribution changed or removed,
open an issue.
