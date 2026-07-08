# Looper Creator

[English](README.md) | [简体中文](README.zh-CN.md)

Looper Creator is a Codex skill for creating **Recursive Loop Orchestration**
projects: structured, token-aware, multi-agent-capable loops that decompose a
goal into verifiable work and stop on machine-checkable conditions.

The project is intentionally strict: vague goals, missing clarification policy,
missing verifiers, missing stop conditions, unbounded subagents, and silent
fallback paths are rejected instead of hidden.

[![Awesome](https://awesome.re/badge.svg)](AWESOME-LOOP-ENGINEERING.md)
[![CI](https://github.com/l8ai-cn/looper-creator/actions/workflows/ci.yml/badge.svg)](https://github.com/l8ai-cn/looper-creator/actions/workflows/ci.yml)

## Quick Links

- [Bilingual learning resources](AWESOME-LOOP-ENGINEERING.md)
- [Manifest schema](skills/looper-creator/schemas/loop-manifest.schema.json)
- [Example loop manifests](skills/looper-creator/examples)
- [Generated project templates](skills/looper-creator/assets/templates)

## Learning Resources

See [Awesome Loop Engineering](AWESOME-LOOP-ENGINEERING.md) for bilingual
courses, primary references, GitHub projects, and the sources that shaped
Looper Creator.

It includes existing Awesome lists, Anthropic/OpenAI/LangGraph references,
Claude loop progression guidance, Andrew Ng and DeepLearning.AI courses, GitHub
projects, runtime standards, and a source-to-schema mapping for Looper Creator.

## Support This Project

If Looper Creator helps you design safer agent loops, please support the project
on GitHub:

- Star the repository to bookmark it and help others discover it.
- Watch the repository if you want schema, template, and adapter updates.
- Fork the repository to adapt the skill for your own agent runtime or team
  workflow.

## What It Builds

A generated loop project contains:

```text
LOOP.md
PROGRESS.md
ACCEPTANCE.md
DECISIONS.md
loop.json
loops.json
tasks.json
agents.json
context-policy.json
state.json
journal.jsonl
runtime.json
monitoring-plan.json
scripts/verify.sh
ADAPTERS.md
AGENTS.md
```

`AGENTS.md` is shown above because the default runtime target is `codex`.
Generate other runtime adapters explicitly with `--runtime-target`.

The v2 manifest models:

- recursive loop nodes
- atomic task decomposition
- acceptance checklist items that must be checked only after verifier-backed
  evidence exists
- secondary user queries for ambiguous requests
- multi-agent collaboration and subagent activation policy
- execution adapters for Codex, Claude Code, Cursor, and portable runtimes
- context/token budget strategy
- blocked-state handling with user-confirmed proxy decisions and supervisor
  drift monitoring
- deterministic verification and anti-gaming rules
- success, failure, budget, no-progress, human-gate, and escalation exits
- common templates for feature development, testing/debugging, browser-based
  website testing, deployment, documentation, bid writing, and generic tasks

## Repository Layout

```text
skills/looper-creator/
  SKILL.md
  agents/openai.yaml
  scripts/create_loop_project.py
  scripts/validate_loop_project.py
  schemas/loop-manifest.schema.json
  references/template-catalog.md
  examples/
  assets/templates/
  tests/
```

## Install

Copy or symlink `skills/looper-creator` into your Codex skills directory:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/looper-creator "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Then ask Codex:

```text
Use $looper-creator to create a verified recursive loop project for my goal.
```

## Validate

Validate the skill metadata:

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py skills/looper-creator
```

Validate all examples:

```bash
for f in skills/looper-creator/examples/*.loop.json; do
  case "$f" in
    *invalid*) python3 skills/looper-creator/scripts/validate_loop_project.py "$f" && exit 1 || true ;;
    *) python3 skills/looper-creator/scripts/validate_loop_project.py "$f" ;;
  esac
done
```

Generate and validate a sample loop project:

```bash
python3 skills/looper-creator/scripts/create_loop_project.py \
  --manifest skills/looper-creator/examples/feature-development.loop.json \
  --output /tmp/example-loop

python3 skills/looper-creator/scripts/validate_loop_project.py /tmp/example-loop
```

Run tests:

```bash
python3 -m unittest discover -s skills/looper-creator/tests
```

## Contract

The public contract is `skills/looper-creator/schemas/loop-manifest.schema.json`.
The dependency-free semantic validator is
`skills/looper-creator/scripts/validate_loop_project.py`.

The schema is English-first and locale-aware through `metadata.locale`; user-facing
content can be localized while structural fields remain stable.

Each manifest must define `acceptance_checklist`. Generated projects write it to
`ACCEPTANCE.md` by default. During execution, agents update one checkbox at a
time only after its acceptance criteria, verifier refs, and evidence refs are
satisfied. If `state.json` reaches `complete`, `scripts/verify.sh` rejects any
remaining unchecked item.

Each manifest must also define `decision_policy`. Generated projects write
blocked-state guidance to `DECISIONS.md` and cadence-based drift checks to
`monitoring-plan.json`. A proxy decision agent may resolve only user-confirmed,
low-risk blocked states; high-risk, irreversible, authority-unclear, or
outward-facing actions still escalate to the user.

The semantic validator also checks contracts that JSON Schema cannot express:
`context_policy.durable_memory` must match `state`, every atomic task must have
one checklist item, and checklist criteria, verifier refs, and evidence refs must
include the task's own acceptance criteria, verifier refs, and output artifacts.

## Public Repository

The project is published at
[github.com/l8ai-cn/looper-creator](https://github.com/l8ai-cn/looper-creator).

Clone it with:

```bash
git clone https://github.com/l8ai-cn/looper-creator.git
cd looper-creator
```

## Runtime Adapters

`loop.json` is the canonical manifest. `runtime.json` records the selected
runtime adapter for a generated project.

By default, project roots generate only the Codex adapter:

```bash
python3 skills/looper-creator/scripts/create_loop_project.py \
  --manifest skills/looper-creator/examples/feature-development.loop.json \
  --output /tmp/example-loop \
  --runtime-target codex
```

Generate another root adapter explicitly:

```bash
python3 skills/looper-creator/scripts/create_loop_project.py \
  --manifest skills/looper-creator/examples/feature-development.loop.json \
  --output /tmp/claude-loop \
  --runtime-target claude_code
```

Runtime-specific files are generated from `execution_adapters`:

- Codex: `AGENTS.md`
- Claude Code: `CLAUDE.md` and optional `.claude/settings.json`
- Cursor: `.cursor/rules/looper-creator.mdc`
- Portable: generic files only

Unselected runtime adapter files are not generated at the project root. When
`--force` regenerates a project for a different runtime, stale unselected adapter
files are removed.

Adapter limits must not weaken verification. If a runtime cannot support a
declared capability, the required behavior is `block_and_report`.

## License

MIT
