# Agent Runtime Adapters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a platform adapter layer so Looper Creator can generate and validate Codex, Claude Code, Cursor, and portable loop execution surfaces without weakening the canonical manifest.

**Architecture:** Keep `loop.json` as the canonical manifest. Add `execution_adapters` and `portability_policy` to the v2 contract, validate adapter semantics in `validate_loop_project.py`, and generate platform files in `create_loop_project.py`. Adapter outputs are generated artifacts; unsupported platform capabilities must block and report rather than silently degrade.

**Tech Stack:** Python standard library, JSON Schema document, Codex Skill resources, Markdown/rules files.

---

### Task 1: Adapter Contract Tests

**Files:**
- Modify: `skills/looper-creator/tests/test_validate_loop_project.py`

- [ ] Add `execution_adapters` and `portability_policy` to `recursive_manifest()`.
- [ ] Assert generated projects contain `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/looper-creator.mdc`, and `ADAPTERS.md`.
- [ ] Add a failing test for `unsupported_capability_behavior != block_and_report`.
- [ ] Run `python3 -m unittest discover -s skills/looper-creator/tests` and confirm failure before implementation.

### Task 2: Validator and Schema

**Files:**
- Modify: `skills/looper-creator/scripts/validate_loop_project.py`
- Modify: `skills/looper-creator/schemas/loop-manifest.schema.json`

- [ ] Add required top-level fields `execution_adapters` and `portability_policy`.
- [ ] Validate adapter targets, instruction files, subagent support flags, deterministic hook policy, approval model, context reload model, generated files, and unsupported capability behavior.
- [ ] Validate portability policy keeps `loop.json` canonical and blocks unsupported capability weakening.

### Task 3: Generator Output

**Files:**
- Modify: `skills/looper-creator/scripts/create_loop_project.py`

- [ ] Generate `ADAPTERS.md` for all manifests with adapter summaries.
- [ ] Generate `AGENTS.md` for Codex adapters.
- [ ] Generate `CLAUDE.md` and `.claude/settings.json` when requested by Claude Code adapters.
- [ ] Generate `.cursor/rules/looper-creator.mdc` when requested by Cursor adapters.
- [ ] Ensure project validation checks adapter-generated files.

### Task 4: Examples and Docs

**Files:**
- Modify: `skills/looper-creator/examples/*.loop.json`
- Modify: `skills/looper-creator/SKILL.md`
- Modify: `README.md`
- Modify: `skills/looper-creator/references/template-catalog.md`

- [ ] Regenerate valid examples with adapter policies.
- [ ] Keep invalid example rejected due missing adapter/portability fields.
- [ ] Document target-specific generated files and non-fallback behavior.

### Task 5: Verification and Commit

**Files:**
- Sync to: `/Users/wwyz/.codex/skills/looper-creator`

- [ ] Run skill validation, JSON validation, unittest, all example validation, generated project validation, and generated verifier.
- [ ] Remove `__pycache__` artifacts.
- [ ] Sync installed skill copy and validate it.
- [ ] Commit with message `Add agent runtime adapters`.
