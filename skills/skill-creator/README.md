# skill-creator

**Create new skills, improve existing ones, and measure skill performance.**

## What it does

Anthropic's official skill-authoring skill (from [anthropics/skills](https://github.com/anthropics/skills)), adapted for CLI. It runs the full author-and-iterate loop:

- **Capture intent -> draft SKILL.md** - what the skill enables, when it triggers (the description is the primary triggering mechanism), the output format.
- **Test cases + evals** - realistic test prompts, run with-skill vs baseline subagents, grade against assertions.
- **Benchmark** - `scripts/aggregate_benchmark.py` produces pass-rate/time/token stats with variance; an eval-viewer renders the results for human review.
- **Iterate** - improve based on feedback, re-run, repeat until satisfied.
- **Description optimization** - `scripts/run_loop.py` splits eval queries train/test, evaluates the current description (3x per query for a reliable trigger rate), proposes improvements, and selects the best by held-out test score.
- **Package** - `scripts/package_skill.py` emits a `.skill`.

## Why it works

A skill used a million times across many prompts is only worth writing if it generalizes - so this skill is built around *measurement*: test prompts, quantitative benchmarks with variance, and a triggering optimizer, rather than vibes. The description-optimization loop is the highest-leverage part: skills under-trigger by default, and the loop tunes the one field that decides whether Claude consults the skill at all.

Paired with `install-skill`: skill-creator authors the folder, install-skill packages, verifies, and installs it.

## How to use

Say "create a skill", "improve/optimize this skill", "run evals", "benchmark a skill", or "optimize a skill's description". It figures out where you are in the create -> test -> review -> improve loop and jumps in.

## Key files

| Path | Purpose |
|---|---|
| `SKILL.md` | The full authoring loop (create / test / improve / optimize) |
| `scripts/run_loop.py` | Automated description-triggering optimizer |
| `scripts/run_eval.py` | Run a single eval |
| `scripts/aggregate_benchmark.py` | Pass-rate / time / token benchmark with variance |
| `scripts/package_skill.py` | Emit a `.skill` |
| `scripts/improve_description.py` | Propose a better description from failures |
| `eval-viewer/generate_review.py` | Render outputs + benchmark for human review |
| `agents/{grader,comparator,analyzer}.md` | Grading, blind A/B, and analysis subagents |
| `references/schemas.md` | JSON structures for evals/grading/benchmark |

---

**Related:** pairs with [install-skill](../install-skill/) - skill-creator authors and measures, install-skill packages and installs. See the [root README](../../README.md) for how the skills interlock and navigate.
