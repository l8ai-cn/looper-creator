# Recursive Loop Orchestration Schema Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade Looper Creator from a single-loop manifest into a research-backed recursive loop orchestration contract for token-efficient, multi-agent, verifiable task execution.

**Architecture:** Keep `SKILL.md` concise and move detailed loop design knowledge into references. Make `loop-manifest.schema.json` the public contract, `validate_loop_project.py` the dependency-free semantic validator, and `create_loop_project.py` the deterministic skeleton generator. Examples become domain templates that exercise the contract.

**Tech Stack:** Python standard library, JSON Schema document, Codex Skill metadata, shell verifier template, GitHub Actions.

---

### Task 1: Add V2 Contract Tests

**Files:**
- Modify: `skills/looper-creator/tests/test_validate_loop_project.py`

- [ ] **Step 1: Add a minimal recursive v2 manifest fixture in the test file**

Create a helper that returns a `RecursiveLoopOrchestration` manifest with:
- `clarification_policy`
- `decomposition_policy`
- nested `loop_nodes`
- `atomic_tasks`
- `agents`
- `collaboration_policy`
- `context_policy`
- `termination_policy`
- `verification_policy`
- `cost_policy`
- `risk_policy`
- `failure_modes`
- `templates`

- [ ] **Step 2: Add tests that fail against the current v1 validator**

Expected failures before implementation:
- v2 manifest is rejected because current validator requires schema version `1.0`.
- generated project lacks `tasks.json`, `agents.json`, and `loops.json`.
- missing `clarification_policy` is not reported with the new error message.

Run:

```bash
python3 -m unittest discover -s skills/looper-creator/tests
```

Expected: FAIL.

### Task 2: Implement V2 Semantic Validation

**Files:**
- Modify: `skills/looper-creator/scripts/validate_loop_project.py`
- Modify: `skills/looper-creator/schemas/loop-manifest.schema.json`

- [ ] **Step 1: Replace the v1 top-level contract with v2 required fields**

Required top-level fields:

```text
kind, schema_version, metadata, objective, clarification_policy,
decomposition_policy, loop_nodes, atomic_tasks, agents,
collaboration_policy, context_policy, termination_policy,
verification_policy, cost_policy, risk_policy, failure_modes,
templates, state, observability, human_gates, escalation
```

- [ ] **Step 2: Add validators for recursive loop nodes**

Validate each node has:
- `id`
- `type`
- `purpose`
- `entry_conditions`
- `exit_conditions`
- `steps`
- `context_pack`
- `verification_refs`
- optional recursive `children`

- [ ] **Step 3: Add validators for task decomposition**

Validate each atomic task has:
- `id`
- `goal`
- `input_refs`
- `output_artifacts`
- `dependencies`
- `assigned_agent`
- `acceptance_criteria`
- `verification_refs`
- `max_attempts`
- `estimated_token_budget`

- [ ] **Step 4: Add validators for clarification, context, collaboration, and termination**

Reject manifests that lack:
- secondary user query behavior for semantic ambiguity
- explicit context budget and trimming policy
- subagent activation criteria and token budget policy
- success, failure, budget, no-progress, and human-gate exits

Run:

```bash
python3 -m unittest discover -s skills/looper-creator/tests
```

Expected: tests move closer to green; generation may still fail until Task 3.

### Task 3: Update Generator Outputs

**Files:**
- Modify: `skills/looper-creator/scripts/create_loop_project.py`

- [ ] **Step 1: Render v2 project artifacts**

Generate:
- `loop.json`
- `LOOP.md`
- `PROGRESS.md`
- `state.json`
- `journal.jsonl`
- `loops.json`
- `tasks.json`
- `agents.json`
- `context-policy.json`
- `scripts/verify.sh`

- [ ] **Step 2: Ensure generated verifier is executable**

Run:

```bash
rm -rf /tmp/looper-creator-v2-example
python3 skills/looper-creator/scripts/create_loop_project.py \
  --manifest skills/looper-creator/examples/feature-development.loop.json \
  --output /tmp/looper-creator-v2-example
python3 skills/looper-creator/scripts/validate_loop_project.py /tmp/looper-creator-v2-example
```

Expected: both commands exit 0.

### Task 4: Replace Examples and Templates

**Files:**
- Replace: `skills/looper-creator/examples/minimal-valid.loop.json`
- Replace: `skills/looper-creator/examples/invalid-vague-goal.loop.json`
- Create: `skills/looper-creator/examples/feature-development.loop.json`
- Create: `skills/looper-creator/examples/testing-debugging.loop.json`
- Create: `skills/looper-creator/examples/deployment-release.loop.json`
- Create: `skills/looper-creator/examples/documentation-writing.loop.json`
- Create: `skills/looper-creator/examples/bid-document-writing.loop.json`
- Create: `skills/looper-creator/examples/generic-task.loop.json`
- Modify: `skills/looper-creator/assets/templates/LOOP.md`
- Modify: `skills/looper-creator/assets/templates/PROGRESS.md`
- Create: `skills/looper-creator/assets/templates/tasks.json`
- Create: `skills/looper-creator/assets/templates/agents.json`

- [ ] **Step 1: Make examples cover domain templates**

Each valid example must include recursive loop nodes, atomic tasks, context strategy, multi-agent activation policy, and deterministic verification.

- [ ] **Step 2: Keep one invalid example that proves semantic ambiguity is rejected**

The invalid example must fail due to vague objective, missing clarification policy, weak verifier, and missing no-progress exit.

### Task 5: Update Skill and README

**Files:**
- Modify: `skills/looper-creator/SKILL.md`
- Modify: `README.md`
- Modify: `.github/workflows/ci.yml`

- [ ] **Step 1: Rewrite SKILL.md around recursive orchestration**

Keep it under 500 lines and point to schema/examples rather than duplicating the whole contract.

- [ ] **Step 2: Update README commands and explanation**

Document v2 scope, template examples, local validation, and GitHub readiness.

- [ ] **Step 3: Update CI to validate all v2 examples**

Ensure invalid example is expected to fail.

### Task 6: Verify, Sync, and Commit

**Files:**
- Sync to: `/Users/wwyz/.codex/skills/looper-creator`

- [ ] **Step 1: Run all validation**

Commands:

```bash
python3 /Users/wwyz/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/looper-creator
python3 -m unittest discover -s skills/looper-creator/tests
for f in skills/looper-creator/examples/*.loop.json; do
  case "$f" in
    *invalid*) python3 skills/looper-creator/scripts/validate_loop_project.py "$f" && exit 1 || true ;;
    *) python3 skills/looper-creator/scripts/validate_loop_project.py "$f" ;;
  esac
done
```

- [ ] **Step 2: Sync installed skill copy**

```bash
rm -rf /Users/wwyz/.codex/skills/looper-creator
cp -R skills/looper-creator /Users/wwyz/.codex/skills/looper-creator
python3 /Users/wwyz/.codex/skills/.system/skill-creator/scripts/quick_validate.py /Users/wwyz/.codex/skills/looper-creator
```

- [ ] **Step 3: Commit local changes**

```bash
git add .
git commit -m "Upgrade looper creator schema to recursive orchestration"
```
