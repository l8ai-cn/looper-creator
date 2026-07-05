---
name: looper-creator
description: Create standardized, verifiable loop projects for autonomous or semi-autonomous agents. Use when the user asks to create, scaffold, initialize, package, harden, or standardize an agent loop, long-running workflow, self-running agent, Ralph-style loop, cron/heartbeat/hook/goal loop, auto-fixer, monitor, or any project that should keep iterating until a machine-checkable condition is met.
---

# Looper Creator

## Purpose

Use this skill to create a loop project, not merely describe one. A valid output
must include durable state, deterministic verification, explicit exits, budget
limits, no-progress detection, and a human escalation path.

This skill complements `loop-engineering`: use loop-engineering principles to
design the loop, then use this skill's contract and scripts to generate and
validate a concrete project skeleton.

## Non-Negotiables

Reject or pause any loop request that cannot define these fields:

- Trigger: heartbeat, cron, hook, or goal.
- Observation: the single check performed each cycle.
- Action: one scoped action per cycle.
- Success: a machine-checkable condition.
- Failure: an unrecoverable or retry-exhausted condition.
- Verifier: a deterministic command or external check.
- Budgets: max iterations, wall-clock cap, and token/cost cap when applicable.
- No-progress rule: a fingerprint and stale-iteration threshold.
- State: file paths for current state and append-only journal.
- Escalation: owner, channel, condition, and human-readable message.
- Human gate: any irreversible or outward-facing action that must stop for approval.

Do not create fallback paths, silent degradation, or "best effort" success states
to make a vague loop look valid. A loop without a verifier or stop condition is
blocked, not partially complete.

## Workflow

1. **Create the loop manifest**
   - Copy `examples/minimal-valid.loop.json` or write an equivalent manifest.
   - Use `schemas/loop-manifest.schema.json` as the contract reference.
   - Keep secrets out of the manifest. Store only secret references.

2. **Validate before generating**
   - Run:
     ```bash
     python3 skills/looper-creator/scripts/validate_loop_project.py path/to/loop.json
     ```
   - Fix any contract failures before scaffolding files.

3. **Generate the project skeleton**
   - Run:
     ```bash
     python3 skills/looper-creator/scripts/create_loop_project.py \
       --manifest path/to/loop.json \
       --output path/to/output-loop-project
     ```

4. **Validate the generated project**
   - Run:
     ```bash
     python3 skills/looper-creator/scripts/validate_loop_project.py path/to/output-loop-project
     ```
   - A valid project contains `LOOP.md`, `PROGRESS.md`, `loop.json`,
     `state.json`, `journal.jsonl`, and `scripts/verify.sh`.

5. **Report honestly**
   - State the generated path, validation command, and result.
   - Report blocked fields, missing external systems, or unverifiable conditions.
   - Do not claim the loop is production-ready until the user's real verifier
     succeeds against the real target system.

## Manifest Guidance

Use precise, checkable language:

- Good success: `python3 scripts/verify.sh exits 0 after checking CI status and
  smoke-test output for run_id`.
- Bad success: `the code looks better`.
- Good no-progress fingerprint: `["git_head", "failing_test_names", "open_task_ids"]`.
- Bad no-progress fingerprint: `["overall progress"]`.

Use a goal loop only when the goal has a deterministic endpoint. Use heartbeat or
cron when cost needs to be bounded by cadence. Use hook only with rate limiting
and backpressure.

## Resource Map

- `scripts/create_loop_project.py`: Generate the standard loop project skeleton
  from a validated manifest.
- `scripts/validate_loop_project.py`: Validate a manifest or generated project
  without external dependencies.
- `schemas/loop-manifest.schema.json`: Machine-readable manifest contract.
- `examples/minimal-valid.loop.json`: Small valid manifest to copy.
- `examples/invalid-vague-goal.loop.json`: Rejected pattern showing what not to
  accept.
- `assets/templates/`: Human-readable template files mirrored by the generator.

## Acceptance Criteria

Before finishing a Looper Creator task, verify:

- The manifest validates.
- The generated project validates.
- Required files exist at the generated path.
- The verifier command is present and executable.
- The final response includes any remaining real-world verification gaps.
