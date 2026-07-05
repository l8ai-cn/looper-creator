# Looper Creator

Looper Creator is a Codex skill for creating **Recursive Loop Orchestration**
projects: structured, token-aware, multi-agent-capable loops that decompose a
goal into verifiable work and stop on machine-checkable conditions.

The project is intentionally strict. Vague goals, missing clarification policy,
missing verifiers, missing stop conditions, unbounded subagents, and silent
fallback paths are rejected instead of hidden.

## What It Builds

A generated loop project contains:

```text
LOOP.md
PROGRESS.md
loop.json
loops.json
tasks.json
agents.json
context-policy.json
state.json
journal.jsonl
scripts/verify.sh
```

The v2 manifest models:

- recursive loop nodes
- atomic task decomposition
- secondary user queries for ambiguous requests
- multi-agent collaboration and subagent activation policy
- context/token budget strategy
- deterministic verification and anti-gaming rules
- success, failure, budget, no-progress, human-gate, and escalation exits
- common templates for feature development, testing/debugging, deployment,
  documentation, bid writing, and generic tasks

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

## License

MIT
