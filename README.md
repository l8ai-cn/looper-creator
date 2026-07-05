# Looper Creator

Looper Creator is a Codex skill for creating standardized autonomous or
semi-autonomous loop projects. It turns a loop idea into a concrete project
skeleton with a manifest, durable state, progress log, verifier script, budget
limits, no-progress detection, and escalation rules.

The skill is intentionally strict: vague goals, missing verifiers, missing stop
conditions, and silent fallback paths are rejected instead of hidden.

## Repository Layout

```text
skills/looper-creator/
  SKILL.md
  agents/openai.yaml
  scripts/create_loop_project.py
  scripts/validate_loop_project.py
  schemas/loop-manifest.schema.json
  examples/
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
Use $looper-creator to create a verified autonomous loop project for my goal.
```

## Local Validation

Validate the skill metadata:

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py skills/looper-creator
```

Validate the example manifest:

```bash
python3 skills/looper-creator/scripts/validate_loop_project.py \
  skills/looper-creator/examples/minimal-valid.loop.json
```

Generate and validate a sample loop project:

```bash
python3 skills/looper-creator/scripts/create_loop_project.py \
  --manifest skills/looper-creator/examples/minimal-valid.loop.json \
  --output /tmp/example-loop

python3 skills/looper-creator/scripts/validate_loop_project.py /tmp/example-loop
```

Run tests:

```bash
python3 -m unittest discover -s skills/looper-creator/tests
```

## Contract

A valid loop manifest must define:

- trigger pattern
- observation and action
- machine-checkable success condition
- failure condition
- deterministic verifier
- iteration/time/token/cost budgets
- no-progress fingerprint and threshold
- durable state and journal files
- escalation path
- human gates for irreversible actions

## License

MIT
