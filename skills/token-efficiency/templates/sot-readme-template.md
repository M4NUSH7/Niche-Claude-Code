# SoT Keyword Index

<!-- The single source of truth for keyword categorization in this project.
     Agents read this BEFORE exploring code or logs, then grep the tags.
     Mirror of the sot_keywords table in .agents/memory.db.
     Seed categories from the project goal at init; promote IDX entries at
     frequency >= 5 during checkpoints. -->

Project goal: {one sentence - categories below derive from this}

## Categories

| Tag | Meaning | Used in | Key locations |
|---|---|---|---|
| [SOT:CONFIG] | Environment, settings, feature flags | code + logs | {e.g. src/config/} |
| [SOT:DB] | Schema, migrations, queries | code + logs | |
| [SOT:API] | Endpoints, contracts, versioning | code + logs | |
| [SOT:AUTH] | Authentication and authorization | code + logs | |
| [SOT:TEST] | Test setup, fixtures, known-flaky | code + logs | |
| [SOT:BUILD] | Build, packaging, CI | code + logs | |
| [SOT:DEPLOY] | Deployment and infra | code + logs | |

<!-- Replace/extend the defaults to fit the project goal at init. -->

## Individually indexed (one-offs, frequency < 5)

| Tag | Meaning | Location | Frequency |
|---|---|---|---|
| [SOT:IDX:example] | {what this one-off marks} | {file:line} | 1 |

## Conventions

- Tags always live inside comments: `// [SOT:AUTH:jwt-refresh]`, `# [SOT:DB:migrations]`.
- Discovery: `rtk grep -rn "\[SOT:AUTH" src/` - never blind-scan.
- Logs: every entry in .agents/memory.db (or {agent-name}/logs/) starts with its tags.
