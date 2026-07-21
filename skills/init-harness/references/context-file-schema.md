# Context file - schema and the ask-vs-infer boundary

`project-context.yml` at repo root. Template: `templates/project-context.yml`.

**Be honest about what it's for.** A 4-question interview extracts the same information. The
context file earns its place through **reviewability**: it's diffable, committable, and
re-runnable - you can see in git *why* the harness is shaped the way it is. Its value is not
automation (that already exists in `sync_harness.py`).

## The boundary

The rule that matters: **anything mechanical is inferred; anything carrying judgment is asked.**

### Inferred - never ask

| Field | Derived from |
|---|---|
| `project` | `project:` or the directory name |
| `toolchain.python` | **preflight, by execution** - never trust a literal |
| `sharedWritePaths` | kit default (`.bld/**`, `memory/**`, `context/**`, docs...) |
| `readGuard` / `gateGuard` / `logging` | kit defaults |
| `skills.available` core four | ponytail, code-review, security-pass, deep-research |
| `docRouting` | `architecture/*.md` **that actually exist on disk** |
| `sot.categories` | seeded from `goal:` prose |
| `sessionDefault` | Opus latest |
| `models{}` | kit tiers unless the user says otherwise |

### Asked - never guess

| Field | Why |
|---|---|
| `domains` (terminal split) | The concurrency contract. Prose like *"a data pipeline and a dashboard"* does **not** tell you whether that's 2 terminals or 1 with 2 phases. Guessing wrong silently splits or merges ownership. |
| `gates` (topology) | A wrong gate **silently unblocks work that should be blocked** - the exact failure audit #2 exists to prevent. Never infer a dependency from prose. |
| `sensitive_paths` | Wrong here = security review doesn't escalate where it must. |
| `models{}` (if non-default) | Cost and quality. The user's call. |

**Recommended defaults when unstated:** single terminal (`t1`), `scaffold-complete` only, kit
sensitive paths filtered to real dirs, kit model tiers. A single terminal is a safe default - you
can split later; you cannot un-ship a wrong gate topology that let work through.

## Field notes

**`python: auto`** - the only correct value in most cases. Preflight enumerates candidates,
**executes** each, rejects Store stubs and virtualenvs, and pins the verified absolute path. A
literal here is a promise the file cannot keep.

**`goal:`** - prose, used *only* for SoT category seeding. It must never reach gate or terminal
inference. This separation is deliberate: an LLM reading "then we validate and promote" will
happily invent a `validated` gate that nobody agreed to.

**`domains[].paths`** - globs. `gate_guard.py` matches writes against these, so they must match
real layout. Offer only directories that exist.

**`domains[].never_blocked`** - at least one terminal should have it, or a stalled gate stalls
everything. The product plane is the usual pick: it builds against schemas, not implementations.

**`gates`** - the tag is the mechanism, the description is for humans. GATE lines in
`.bld/*/phases.md` must contain the **exact** tag string.

**`doc_routing`** - by **filename**, never by number. Renumbering silently breaks routing.

## Worked example - a non-trading project (proving reusability)

```yaml
project: pipeline-observer
platform: linux
python: auto
goal: >
  Ingest Kafka events, validate against Avro contracts, expose a metrics API
  and an ops dashboard.

domains:
  - name: core / contracts / ingest
    paths: ["packages/**", "contracts/**", "ingest/**"]
    owns_gates: [scaffold-complete]
    blocked_until: []
  - name: metrics API
    paths: ["services/api/**"]
    blocked_until: [scaffold-complete]
  - name: ops dashboard
    paths: ["apps/dashboard/**"]
    never_blocked: true

gates:
  scaffold-complete: {owner: t1, description: "Scaffold done; API may start"}

sensitive_paths: ["**/auth/**", "**/admin/**"]
domain_reviewer: design-reviewer
doc_routing:
  api:      architecture/02_api.md
  security: architecture/08_security.md
```

Nothing trading-specific. What varies per project: `domains`, `gates`, `sensitive_paths`,
`domain_reviewer`, `doc_routing`, and the SoT seed. Everything else is universal.

**Naming note (N4):** `project-context.yml` uses snake_case (`domain_reviewer`, matching its
sibling fields `blocked_until`/`owns_gates`/`sensitive_paths`); `harness.config.json` and the
generated agent slot use kebab-case (`domain-reviewer`, matching every other agent key in that
file). This is a deliberate per-format convention, not drift - the intake interview/YAML speaks
snake_case, the JSON config and `.claude/agents/*.md` filenames speak kebab-case, and the
mapping between the two is exactly this one field. Do not "fix" one to match the other.
