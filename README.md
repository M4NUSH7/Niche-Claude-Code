# Niche Claude Code Skills

A curated set of **Agent Skills** for Claude Code (and Cowork) that make an agent
cheaper, more disciplined, and better at large multi-step builds - without
losing output quality. Each skill is self-contained, verifiable, and installable
as a plain folder (Code) or a `.skill` upload (Cowork).

---

## Quickstart

**Claude Code (CLI or the desktop Code tab):**

```bash
git clone https://github.com/M4NUSH7/Niche-Claude-Code
cd Niche-Claude-Code

# 1. Install the skills you want (they are plain folders).
#    macOS / Linux:
cp -r skills/token-efficiency skills/init-harness skills/ponytail ~/.claude/skills/
#    ...or just the ones you need.
```

```powershell
# Windows (mirror-copy each skill folder; never /MIR the shared parent):
robocopy "skills\token-efficiency" "$env:USERPROFILE\.claude\skills\token-efficiency" /MIR
```

```bash
# 2. Turn on the always-on defaults (routing + concise output every turn):
#    append this ~100-token block to your ~/.claude/CLAUDE.md
cat skills/token-efficiency/templates/CLAUDE-md-snippet.md >> ~/.claude/CLAUDE.md
```

Then just work - the skills trigger on their own descriptions (e.g. say
`/init-harness` to scaffold a build harness, "be lazy" for ponytail, or run a dev
command with `rtk` prefixed). Skills that wrap a tool install it on first use:
`uv tool install graphifyy`, `uv tool install "scrapling[all]" && scrapling install`.

**Cowork (desktop app):** don't copy folders - Cowork loads from your claude.ai
account. Upload the `.skill` files from [`skills/cowork/`](skills/cowork/) via
**Customize -> Skills -> upload**. Use the `-cowork` editions (they bundle the
Linux build of any native binary).

New here? Read [Why the model choices](#why-the-model-choices-its-not-about-cost)
to understand the core idea, then [Navigating this repo](#navigating-this-repo-skills-links-configs)
to find your way around. Full install detail is under [Installing](#installing).

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

## Double your Claude usage at the same output quality

The point of this stack is simple: **get roughly twice as much done within the same
Claude usage, with no drop in output quality.** Four levers compound on a typical
agentic coding session, and every one of them cuts *waste*, never substance:

| Lever | Skill | What it removes |
|---|---|---|
| Command-output compression | [token-efficiency](skills/token-efficiency/) (RTK) | 60-90% of the git/test/build log volume the agent reads |
| Query instead of re-read | [graphify](skills/graphify/) + token-efficiency | redundant file reads - navigate a code-graph once instead of re-reading files every turn |
| No narration / recaps | token-efficiency (output contract) | "Let me.../Now I'll..." narration, status theater, and echoing what a command already printed |
| Right model per task | token-efficiency (routing) | wrong-model overhead - the heavy model only where it's needed |

What is **never** cut: the code, the reasoning that reaches a non-obvious answer,
requested explanations, or error diagnoses - those are explicitly protected. The
savings come entirely from narration, redundant context, and wrong-model overhead.

On top of the raw per-turn savings, the build-discipline skills (enforced
definition-of-done, bounded retries, scoped handoffs) remove the *silent* waste -
hallucination loops and re-work - that stretches a task across far more turns than
it needs. That compounding is where "double your usage" actually comes from.

> Benchmarks: measured before/after numbers will be added here.

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

## Why the model choices (it's not about cost)

The routing rules pin **cheaper, older-tier models for subagents** - coders on a
Sonnet tier, logging on Haiku - and keep the newest, most powerful model for the
**top-level session** only. The reason is not cost; it's a bet about **where model
capability actually matters**:

- **A model does not need to be the smartest available to write good code - it needs
  a specific enough route.** A frontier model earns its price when the task is
  open-ended: deciding *what* to build, decomposing it, resolving ambiguity. Once
  that thinking is done and the task is a **frozen, well-specified contract** - a
  Goal Packet with machine-checkable `success_criteria`, explicit `scope_boundaries`,
  and exact `inputs`/`outputs` - a mid-tier model produces output that is
  effectively indistinguishable from the frontier model's, because there is nothing
  left to be smart *about*. The intelligence was spent upstream, in the routing.
- **So the split is deliberate:** the powerful top-level model does the ambiguous
  planning and review; the cheaper pinned subagents execute the frozen contract.
  Give a mid-tier coder a vague prompt and quality drops; give it a precise Goal
  Packet and it matches the frontier model on the part that's left - the mechanical
  generation. This is exactly why [init-harness](skills/init-harness/)'s goal-packet
  discipline and [token-efficiency](skills/token-efficiency/)'s routing are designed
  together: **routing to a cheaper model is only safe because the handoff is
  specific**, and the handoff is made specific precisely so routing is safe.
- **Pinning is by full model ID, not a tier alias.** A bare alias (`sonnet`,
  `opus`) silently resolves to *latest of that tier* and overrides the pin - so the
  ID is pinned in the agent's frontmatter and no `model:` arg is passed at spawn.
  The **top-level** session is the one place "latest" is correct (it floats to the
  newest model automatically); for subagents, "latest" is the footgun.

Net: you are not trading quality for cost. You are spending frontier-model
capability where it changes the outcome (the route), and mid-tier capability where
it doesn't (executing the route) - which is what makes the same Claude usage go
roughly twice as far.

---

## Navigating this repo (skills, links, configs)

Everything is cross-linked so you can follow the thread:

- **Start at a skill folder** - each has a `README.md` (what/why/how/install/key-files)
  and a `SKILL.md` (the definition Claude loads).
- **The config that ties it together** is token-efficiency's
  [`templates/CLAUDE-md-snippet.md`](skills/token-efficiency/templates/CLAUDE-md-snippet.md)
  - the ~100-token block you append to `~/.claude/CLAUDE.md` to keep routing + the
  output contract always-on. This is the single knob that makes the whole stack's
  defaults apply every turn.
- **The harness config** is init-harness's
  [`templates/kit/harness.config.json`](skills/init-harness/templates/kit/harness.config.json)
  - the one file that matters when you init a build harness (terminals, gates,
  model tiers, sensitive paths). Its
  [`decision-guide.md`](skills/init-harness/references/decision-guide.md) explains
  the four decisions worth asking.
- **The handoff contract** between orchestrator and subagent is
  [`templates/goal-packet.template.yml`](skills/init-harness/templates/goal-packet.template.yml)
  with the doctrine in
  [`templates/docs/12_graph_of_loops.md`](skills/init-harness/templates/docs/12_graph_of_loops.md).

Follow-the-link map:

| If you want to... | Go to |
|---|---|
| Make Claude cheaper/leaner on every turn | [token-efficiency](skills/token-efficiency/) -> append its [CLAUDE.md snippet](skills/token-efficiency/templates/CLAUDE-md-snippet.md) |
| Run a disciplined multi-terminal build | [init-harness](skills/init-harness/) -> edit [harness.config.json](skills/init-harness/templates/kit/harness.config.json) |
| Understand why cheaper subagents are safe | this section + [init-harness goal packets](skills/init-harness/templates/goal-packet.template.yml) |
| Navigate a codebase without re-reading | [graphify](skills/graphify/) (feed its queries into a Goal Packet's `inputs`) |
| Build or ship a new skill | [skill-creator](skills/skill-creator/) (author) -> [install-skill](skills/install-skill/) (package + install) |
| Scaffold an app to production bar | [production-grade-scaffold](skills/production-grade-scaffold/) -> [ui-standout](skills/ui-standout/) for the UI |
| Keep code minimal / track deferred debt | [ponytail](skills/ponytail/) |
| Scrape a protected site / research a topic | [scrapling](skills/scrapling/) / [agent-reach](skills/agent-reach/) |

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

---

## License

The original work in this repository is licensed under the **[MIT License](LICENSE)**.

Some skills bundle upstream code/content under their own licenses (Apache-2.0,
BSD-3-Clause, Anthropic terms) - those components remain under their upstream
licenses, listed in the NOTICE section of [LICENSE](LICENSE) and credited above.
If you redistribute this repo, keep those upstream notices.
