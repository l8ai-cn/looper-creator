# Loop Template Catalog

Use this catalog to choose the nearest starting template before writing a
manifest. Each template still needs task-specific objective, context, verifier,
budget, and human-gate values.

Every template should also select runtime adapters. Keep `loop.json` canonical
and generate platform files from `execution_adapters`; do not edit adapter files
as the source of truth.

## feature-development

Use for one scoped software feature. Start with clarification, decompose into
source/test/review tasks, run deterministic tests per task, and stop before push,
merge, or deploy.

Recommended node pattern:

`clarify -> plan -> recursive implementation cycle -> reviewer gate -> terminal verification`

## testing-debugging

Use for bug fixing and failing tests. Require an initial reproduction, preserve
the failing symptom as evidence, fix the root cause, and verify the regression.
Do not allow fallback, skipped tests, or weakened assertions.

Recommended node pattern:

`reproduce -> isolate -> implement fix -> regression verify -> review`

## deployment-release

Use for release preparation and deployment workflows. Treat deployment as a
human-gated action. Require build evidence, preflight checks, rollback plan,
health checks, and post-release verification.

Recommended node pattern:

`preflight -> package -> verify -> human approval -> deploy -> health check`

## documentation-writing

Use for README, technical docs, API docs, and knowledge-base writing. Decompose
by reader question or page boundary. Require source evidence, link checks, and
review of unsupported claims.

Recommended node pattern:

`research -> outline -> page tasks -> review -> link/format verify`

## bid-document-writing

Use for proposals, tenders, and compliance-heavy documents. Decompose by scored
requirement and final section. Require requirement coverage, evidence mapping,
review, and final compliance verification.

Recommended node pattern:

`parse requirements -> map scoring -> section tasks -> compliance review -> final assembly`

## research-synthesis

Use for research reports where sources and coverage define completion. Require
named sources, coverage criteria, contradiction checks, and source-backed claims.

Recommended node pattern:

`scope -> source retrieval -> evidence extraction -> synthesis -> citation verification`

## generic-task

Use when no domain template fits. Clarify ambiguous goals, recursively split into
verifiable atomic tasks, use subagents only when token economics justify them,
and stop on machine-checkable completion or explicit escalation.

## Adapter Selection

- Use `codex` when the loop will be executed in Codex and should emit `AGENTS.md`.
- Use `claude_code` when the loop should emit `CLAUDE.md` and optional hook
  settings.
- Use `cursor` when the loop should emit Cursor rules.
- Use `portable` when no platform-specific execution surface is known yet.

If the selected runtime lacks a capability, keep the manifest invalid or blocked
until the user chooses an explicit alternative. Do not design silent fallback.
