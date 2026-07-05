---
name: looper-creator
description: Create standardized Recursive Loop Orchestration projects for autonomous or semi-autonomous agents. Use when the user asks to create, scaffold, initialize, package, harden, or standardize an agent loop, recursive task loop, multi-agent workflow, self-running agent, Ralph-style loop, auto-fixer, monitor, browser-based website testing loop, documentation loop, deployment loop, bid-writing loop, or any project that should decompose work and iterate until machine-checkable completion.
---

# Looper Creator

## Purpose

Use this skill to create a concrete loop project, not merely describe one. A
valid project uses `RecursiveLoopOrchestration` schema v2.0 and must define:

- recursive loop nodes, not a fixed one-level macro/micro loop;
- atomic tasks with owners, dependencies, outputs, acceptance criteria, and
  verifier references;
- clarification policy for ambiguous user requests and secondary user queries;
- multi-agent collaboration policy with subagent activation limits;
- execution adapters for Codex, Claude Code, Cursor, and portable runtimes;
- context and token policy for retrieval, trimming, compaction, and durable
  memory;
- deterministic verification, protected verifier paths, and anti-gaming rules;
- browser evidence review rules when a website-testing loop is requested:
  raw findings must be deduplicated, token/JWT evidence must be scrubbed, and
  navigation seeds must not become confirmed bugs without visible-route proof;
- success, failure, budget, no-progress, human-gate, and escalation exits.

Do not design fallback paths, silent degradation, or vague "best effort" terminal
states. Missing verification, unclear authority, or ambiguous success criteria is
a blocked loop, not a valid loop.

## Workflow

1. **Choose the closest template**
   - Read `references/template-catalog.md` when the user asks for a known loop
     type such as feature development, testing/debugging, browser-based website
     testing, deployment, technical documentation, bid writing, research
     synthesis, or generic task execution.
   - Start from a matching file in `examples/` when available.

2. **Clarify before scaffolding**
   - Apply `clarification_policy` before generating files.
   - Ask a secondary user query when goal, acceptance criteria, verification,
     permissions, data impact, production impact, or delivery target is unclear.
   - Make only low-risk assumptions and record them in `PROGRESS.md`.

3. **Write or adapt the manifest**
   - Use `schemas/loop-manifest.schema.json` as the public contract.
   - Keep secrets out of the manifest. Use references, not plaintext credentials.
   - Split work recursively through `loop_nodes`; split executable work through
     `atomic_tasks`.

4. **Validate before generation**
   - Run:
     ```bash
     python3 skills/looper-creator/scripts/validate_loop_project.py path/to/loop.json
     ```
   - Fix root causes. Do not add compatibility branches to make invalid loop
     designs pass.

5. **Generate the project skeleton**
   - Run:
     ```bash
     python3 skills/looper-creator/scripts/create_loop_project.py \
       --manifest path/to/loop.json \
       --output path/to/output-loop-project
     ```

6. **Validate generated output**
   - Run:
     ```bash
     python3 skills/looper-creator/scripts/validate_loop_project.py path/to/output-loop-project
     ```
   - A valid project contains `LOOP.md`, `PROGRESS.md`, `loop.json`,
     `loops.json`, `tasks.json`, `agents.json`, `context-policy.json`,
     `state.json`, `journal.jsonl`, `ADAPTERS.md`, runtime adapter files, and
     `scripts/verify.sh`.

## Design Rules

- Represent task decomposition as a recursive graph of loop nodes. A node may be
  a workflow, agent loop, reflection loop, evaluator-optimizer loop, parallel
  section, handoff loop, or human review gate.
- Treat `loop.json` as the canonical manifest. Platform files such as
  `AGENTS.md`, `CLAUDE.md`, and `.cursor/rules/looper-creator.mdc` are generated
  adapters, not the source of truth.
- Do not weaken verification for platform limits. If a runtime lacks hooks,
  subagents, or another declared capability, block and report rather than
  silently degrading the loop.
- Use multi-agent execution only when the manifest's activation policy justifies
  it: independent tasks, context too large for one agent, independent review
  needed, or domain specialization required.
- Keep shared context small. Put durable truth in files and load detailed
  artifacts just in time.
- Treat tool output as expensive. Preserve commands, exit codes, failing
  assertions, changed paths, and evidence refs; trim noisy raw logs.
- For browser-testing loops, do not trust raw automated findings directly.
  Require a review pass that merges duplicate network failures, rejects
  navigation-abort noise, separates seeded route leads from confirmed visible
  route defects, and scans evidence for passwords, cookies, Authorization
  headers, `access_token` values, and JWT-shaped strings.
- Use deterministic verifiers for per-task, per-loop, and terminal checks. The
  agent's own completion statement is not evidence.
- Stop on no progress by comparing manifest-defined fingerprints, not by asking
  the agent whether it feels stuck.
- Gate irreversible or outward-facing operations such as push, merge, deployment,
  deletion, email, billing, or production data changes.

## Resource Map

- `scripts/create_loop_project.py`: Generate a standard recursive loop project
  from a validated v2 manifest.
- `scripts/validate_loop_project.py`: Validate a manifest or generated project
  using dependency-free semantic checks.
- `schemas/loop-manifest.schema.json`: Machine-readable v2 contract.
- `examples/*.loop.json`: Valid domain templates plus one invalid rejection
  example.
- `references/template-catalog.md`: Template selection guidance.
- `assets/templates/`: Static project skeleton templates.

## Runtime Adapter Targets

- `codex`: generate `AGENTS.md`; subagents are explicit and must respect the
  active sandbox and approval policy.
- `claude_code`: generate `CLAUDE.md` and optional `.claude/settings.json`;
  hooks may enforce checks, but must not bypass verification.
- `cursor`: generate `.cursor/rules/looper-creator.mdc`; rules and subagents
  must remain subordinate to `loop.json`.
- `portable`: generate generic project artifacts when no platform-specific
  runtime is selected.

## Acceptance Criteria

Before finishing a Looper Creator task, verify:

- The manifest validates.
- The generated project validates.
- Required files exist at the generated path.
- The verifier script is executable.
- Any real-world verifier that depends on external systems is either run and
  reported, or explicitly listed as unavailable.
