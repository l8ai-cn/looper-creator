#!/usr/bin/env python3
"""Create a recursive loop project from a Looper Creator v2 manifest."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_loop_project import load_manifest, validate_manifest, validate_project


def _slug(value: str) -> str:
    slug = "".join(char.lower() if char.isalnum() else "-" for char in value)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "loop-project"


def _write(path: Path, content: str, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if executable:
        mode = path.stat().st_mode
        path.chmod(mode | 0o111)


def _json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


def _manifest_name(manifest: dict[str, Any]) -> str:
    return manifest["metadata"]["name"]


def _terminal_verifier(manifest: dict[str, Any]) -> dict[str, Any]:
    verifiers = manifest["verification_policy"]["verifiers"]
    for verifier in verifiers:
        if verifier.get("scope") == "terminal":
            return verifier
    return verifiers[0]


def render_loop_md(manifest: dict[str, Any]) -> str:
    metadata = manifest["metadata"]
    objective = manifest["objective"]
    clarification = manifest["clarification_policy"]
    decomposition = manifest["decomposition_policy"]
    collaboration = manifest["collaboration_policy"]
    context = manifest["context_policy"]
    termination = manifest["termination_policy"]
    verification = manifest["verification_policy"]
    escalation = manifest["escalation"]
    gates = "\n".join(f"- {item}" for item in manifest["human_gates"]["irreversible_actions"]) or "- None"
    roots = "\n".join(f"- `{node['id']}`: {node['purpose']}" for node in manifest["loop_nodes"])
    tasks = "\n".join(f"- `{task['id']}`: {task['goal']}" for task in manifest["atomic_tasks"])
    agents = "\n".join(f"- `{agent['id']}` ({agent['role']}): {', '.join(agent['responsibilities'])}" for agent in manifest["agents"])
    verifiers = "\n".join(f"- `{item['id']}`: `{item['command']}`" for item in verification["verifiers"])

    return f"""# {metadata['name']}

## Purpose

{metadata['description']}

User goal: {objective['user_goal']}

Done definition: {objective['done_definition']}

## Clarification Policy

- Default action: `{clarification['default_action']}`
- Secondary user query: {clarification['secondary_user_query']['prompt']}
- Block if: {', '.join(clarification['block_if'])}
- Assumption record: `{clarification['assumption_policy']['record_path']}`

## Recursive Loop Topology

{roots}

Decomposition strategy: {decomposition['strategy']}

Split until:

{chr(10).join(f"- {item}" for item in decomposition['split_until'])}

## Atomic Tasks

{tasks}

## Agents

{agents}

## Collaboration

- Patterns: {', '.join(collaboration['patterns'])}
- Subagent activation: {', '.join(collaboration['subagent_activation']['allowed_when'])}
- Token policy: {collaboration['subagent_activation']['token_budget_policy']}

## Context Strategy

- Max context tokens: {context['max_context_tokens']}
- Retrieval: {context['retrieval_strategy']}
- Tool output trimming: {context['tool_output_trimming']}
- Compaction trigger: {context['compaction']['trigger_ratio']}
- Durable memory: `{context['durable_memory']['state_path']}`, `{context['durable_memory']['journal_path']}`, `{context['durable_memory']['progress_path']}`

## Termination Policy

- Success: {', '.join(termination['success'])}
- Failure: {', '.join(termination['failure'])}
- Budget exits: {termination['budget_exits']}
- No-progress fields: {', '.join(termination['no_progress']['fingerprint_fields'])}
- Human gates: {', '.join(termination['human_gate'])}

## Verification

{verifiers}

Protected paths:

{chr(10).join(f"- `{item}`" for item in verification['protected_paths'])}

## Human Gates

{gates}

## Escalation

- Condition: {escalation['condition']}
- Owner: {escalation['owner']}
- Channel: {escalation['channel']}
- Message template: {escalation['message_template']}
"""


def render_progress_md(manifest: dict[str, Any]) -> str:
    return f"""# Progress

Loop: {_manifest_name(manifest)}

## Current Status

- Status: planned
- Active loop node: not started
- Active atomic task: not assigned
- Last verifier result: not run
- Last no-progress fingerprint: not recorded
- Current token estimate: 0

## Assumptions

- No assumptions recorded yet.

## Decisions

- Initial recursive loop contract generated from `loop.json`.

## Next Cycle

1. Re-read `loop.json`, `state.json`, `tasks.json`, `agents.json`, and this file.
2. Evaluate `clarification_policy` before acting.
3. Execute one eligible loop node or atomic task.
4. Record evidence and stop on success, failure, budget, no-progress, or human-gate conditions.
"""


def render_state_json(manifest: dict[str, Any]) -> str:
    state = {
        "schema_version": "2.0",
        "loop_id": manifest["metadata"]["id"],
        "loop_name": _manifest_name(manifest),
        "status": "planned",
        "iteration": 0,
        "active_loop_node_id": None,
        "active_task_id": None,
        "started_at": None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "last_verifier_id": None,
        "last_verifier_exit_code": None,
        "last_no_progress_fingerprint": None,
        "stale_iterations": 0,
        "token_estimate": 0,
        "terminal_reason": None,
    }
    return _json(state)


def render_verify_sh(manifest: dict[str, Any]) -> str:
    commands: list[str] = []
    for verifier in manifest["verification_policy"]["verifiers"]:
        if verifier.get("scope") != "terminal":
            continue
        command = verifier["command"]
        if "scripts/verify.sh" not in command:
            commands.append(command)
    if not commands:
        commands = [
            "test -f loop.json",
            "test -f loops.json",
            "test -f tasks.json",
            "test -f agents.json",
            "test -f context-policy.json",
        ]
    body = "\n".join(commands)
    return f"""#!/usr/bin/env bash
set -euo pipefail

# Generated structural verifier. Replace or extend with the real deterministic
# checks for this loop, but do not weaken existing checks without human approval.
{body}
"""


def create_project(manifest: dict[str, Any], output: Path, force: bool = False) -> None:
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("manifest validation failed:\n" + "\n".join(f"- {error}" for error in errors))

    if output.exists() and any(output.iterdir()) and not force:
        raise FileExistsError(f"{output} exists and is not empty; pass --force to overwrite generated files")

    state = manifest["state"]
    output.mkdir(parents=True, exist_ok=True)
    _write(output / "loop.json", _json(manifest))
    _write(output / "LOOP.md", render_loop_md(manifest))
    _write(output / state["progress_path"], render_progress_md(manifest))
    _write(output / state["path"], render_state_json(manifest))
    _write(output / state["journal_path"], "")
    _write(output / "loops.json", _json(manifest["loop_nodes"]))
    _write(output / "tasks.json", _json(manifest["atomic_tasks"]))
    _write(output / "agents.json", _json(manifest["agents"]))
    _write(output / "context-policy.json", _json(manifest["context_policy"]))
    (output / manifest["observability"]["evidence_dir"]).mkdir(parents=True, exist_ok=True)
    _write(output / "scripts" / "verify.sh", render_verify_sh(manifest), executable=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a standard recursive loop project from a manifest.")
    parser.add_argument("--manifest", required=True, help="Path to loop manifest JSON")
    parser.add_argument("--output", help="Output directory. Defaults to manifest metadata.name slug beside the manifest.")
    parser.add_argument("--force", action="store_true", help="Allow writing into an existing non-empty output directory")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    try:
        manifest = load_manifest(manifest_path)
        name = manifest.get("metadata", {}).get("name", "loop-project")
        output = Path(args.output) if args.output else manifest_path.parent / _slug(name)
        create_project(manifest, output, force=args.force)
        errors = validate_project(output)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: created recursive loop project at {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
