# Loop Template Catalog

Use this catalog to choose the nearest starting template before writing a
manifest. Each template still needs task-specific objective, context, verifier,
budget, and human-gate values.

Every template should also declare runtime adapters. Keep `loop.json` canonical,
record the selected generated runtime in `runtime.json`, and generate only the
selected platform files at the project root; do not edit adapter files as the
source of truth.

Every template must include `acceptance_checklist` and generate `ACCEPTANCE.md`.
Use one checkbox per atomic task, bind each item to an owner agent, verifier
refs, and durable evidence refs, and check items only after the evidence exists.

Every template must include `decision_policy` and generate `DECISIONS.md` plus
`monitoring-plan.json`. Add a proxy decision agent for user-confirmed low-risk
blocked states and a supervisor agent for cadence-based goal-drift checks.
Proxy decisions must never approve irreversible, production, credential, billing,
security, merge, push, or deployment actions.

## Loop Primitive Selection

Choose the smallest loop primitive before choosing a domain template:

- **turn-based**: user triggers each run and hands off verification. Use for
  exploratory, one-off, or still-ambiguous work. Optimize by encoding the user's
  manual checks into a skill or verifier.
- **goal-based**: user hands off the stop condition. Use when done is known and
  machine-checkable. Require explicit success, failure, budget, no-progress, and
  human-gate exits.
- **time-based**: user hands off the trigger. Use when the observed source
  changes on a schedule. Match cadence to source change frequency and add rate
  limits/backpressure.
- **proactive**: user hands off a recurring prompt/routine. Use only for
  recurring, well-defined work with bounded per-run goals, pilot evidence,
  usage review, supervisor checks, and human gates.

If a smaller primitive can complete the work, do not promote it to a larger one.
Dynamic workflows that may spawn many agents must run a small pilot before the
full loop is allowed.

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

## website-browser-testing

Use for read-only browser probes of public or authenticated websites, admin
panels, and SaaS apps when the output is an evidence-backed bug list. Require
target URL, credential reference instead of plaintext credentials, mutation
boundary, browser artifacts, console/network summaries, screenshot evidence,
secret/JWT scanning, and a review step that promotes only confirmed defects.

Recommended node pattern:

`scope/safety -> login/app-shell probe -> route/workflow probes -> evidence review -> bug-list verification`

Important review rules:

- Treat `networkidle` as unsafe for apps with polling or WebSockets; prefer DOM
  readiness plus bounded waits.
- Store raw browser logs on disk and put only distilled signatures in context.
- Merge duplicate API failures by endpoint/status.
- Do not promote seeded direct-route 404s unless visible navigation or product
  requirements prove the route is user-facing.
- Scrub passwords, cookies, Authorization headers, `access_token` values, and
  JWT-shaped strings before writing evidence.

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

Scaffolding defaults to `--runtime-target codex`. Generate Claude Code or Cursor
root adapter files only when explicitly requested. Unselected runtime adapters
should remain declared in `loop.json`/`ADAPTERS.md`, not mixed into the generated
project root.

If the selected runtime lacks a capability, keep the manifest invalid or blocked
until the user chooses an explicit alternative. Do not design silent fallback.
