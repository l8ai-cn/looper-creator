# Looper Creator

Looper Creator is a Codex skill for creating **Recursive Loop Orchestration**
projects: structured, token-aware, multi-agent-capable loops that decompose a
goal into verifiable work and stop on machine-checkable conditions.

The project is intentionally strict. Vague goals, missing clarification policy,
missing verifiers, missing stop conditions, unbounded subagents, and silent
fallback paths are rejected instead of hidden.

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
loop.json
loops.json
tasks.json
agents.json
context-policy.json
state.json
journal.jsonl
runtime.json
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

The semantic validator also checks contracts that JSON Schema cannot express:
`context_policy.durable_memory` must match `state`, every atomic task must have
one checklist item, and checklist criteria, verifier refs, and evidence refs must
include the task's own acceptance criteria, verifier refs, and output artifacts.

## Publish To GitHub

This repository is ready for a public GitHub remote once GitHub authentication is
available locally:

```bash
gh auth status
gh repo create looper-creator --public --source . --remote origin --push
```

If the repository already exists, add its remote and push:

```bash
git remote add origin git@github.com:<owner>/looper-creator.git
git push -u origin main
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
