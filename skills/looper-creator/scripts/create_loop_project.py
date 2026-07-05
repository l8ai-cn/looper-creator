#!/usr/bin/env python3
"""Create a recursive loop project from a Looper Creator v2 manifest."""

from __future__ import annotations

import argparse
import json
import shlex
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


def _checklist_path(manifest: dict[str, Any]) -> str:
    return manifest["acceptance_checklist"]["path"]


def _progress_path(manifest: dict[str, Any]) -> str:
    return manifest["state"]["progress_path"]


def _adapter_for_target(manifest: dict[str, Any], target: str) -> dict[str, Any]:
    for adapter in manifest["execution_adapters"]:
        if adapter.get("target") == target:
            return adapter
    raise ValueError(f"runtime target {target!r} is not declared in execution_adapters")


def render_loop_md(manifest: dict[str, Any]) -> str:
    metadata = manifest["metadata"]
    objective = manifest["objective"]
    clarification = manifest["clarification_policy"]
    decomposition = manifest["decomposition_policy"]
    collaboration = manifest["collaboration_policy"]
    context = manifest["context_policy"]
    termination = manifest["termination_policy"]
    verification = manifest["verification_policy"]
    checklist = manifest["acceptance_checklist"]
    escalation = manifest["escalation"]
    gates = "\n".join(f"- {item}" for item in manifest["human_gates"]["irreversible_actions"]) or "- None"
    roots = "\n".join(f"- `{node['id']}`: {node['purpose']}" for node in manifest["loop_nodes"])
    tasks = "\n".join(f"- `{task['id']}`: {task['goal']}" for task in manifest["atomic_tasks"])
    agents = "\n".join(f"- `{agent['id']}` ({agent['role']}): {', '.join(agent['responsibilities'])}" for agent in manifest["agents"])
    verifiers = "\n".join(f"- `{item['id']}`: `{item['command']}`" for item in verification["verifiers"])
    checklist_items = "\n".join(
        f"- `{item['id']}`: {item['description']}" for item in checklist["items"]
    )

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

## Acceptance Checklist

- Path: `{checklist['path']}`
- Update policy: {checklist['update_policy']}

{checklist_items}

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


def render_acceptance_md(manifest: dict[str, Any]) -> str:
    checklist = manifest["acceptance_checklist"]
    progress_path = _progress_path(manifest)
    lines = [
        "# Acceptance Checklist",
        "",
        f"Loop: {_manifest_name(manifest)}",
        "",
        f"Update policy: {checklist['update_policy']}",
        "",
        "## Operating Rules",
        "",
        "- Only change `[ ]` to `[x]` after every acceptance criterion passes.",
        "- Evidence refs must point to existing artifacts, command outputs, screenshots, logs, diffs, or review notes.",
        f"- If later verification invalidates an item, change it back to `[ ]` and record the reason in `{progress_path}`.",
        "- Terminal completion may only be claimed when every checklist item is checked and the terminal verifier passes.",
        "",
        "## Items",
        "",
    ]
    for item in checklist["items"]:
        lines.extend(
            [
                f"- [ ] `{item['id']}`: {item['description']}",
                f"  - Owner agent: `{item['owner_agent']}`",
            ]
        )
        if item.get("task_id"):
            lines.append(f"  - Atomic task: `{item['task_id']}`")
        if item.get("loop_node_id"):
            lines.append(f"  - Loop node: `{item['loop_node_id']}`")
        lines.append("  - Acceptance criteria:")
        lines.extend(f"    - {criterion}" for criterion in item["acceptance_criteria"])
        lines.append("  - Verification refs:")
        lines.extend(f"    - `{ref}`" for ref in item["verification_refs"])
        lines.append("  - Evidence refs:")
        lines.extend(f"    - {ref}" for ref in item["evidence_refs"])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_progress_md(manifest: dict[str, Any]) -> str:
    checklist_path = _checklist_path(manifest)
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

## Acceptance Trace

- Checklist path: `{checklist_path}`
- Checked items: none
- Reopened items: none

## Next Cycle

1. Re-read `loop.json`, `state.json`, `tasks.json`, `agents.json`, `{checklist_path}`, and this file.
2. Evaluate `clarification_policy` before acting.
3. Execute one eligible loop node or atomic task.
4. Record evidence, then check exactly the matching acceptance item only if its criteria and verifier refs pass.
5. Stop on success, failure, budget, no-progress, or human-gate conditions.
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
    checklist_path = shlex.quote(_checklist_path(manifest))
    state_path = shlex.quote(manifest["state"]["path"])
    commands.extend(
        [
            f"test -s {checklist_path}",
            f"grep -Eq -- '- \\[[ xX]\\]' {checklist_path}",
            f"if grep -Eq '\"status\"[[:space:]]*:[[:space:]]*\"complete\"' {state_path}; then ! grep -Eq -- '- \\[ \\]' {checklist_path}; fi",
        ]
    )
    body = "\n".join(commands)
    return f"""#!/usr/bin/env bash
set -euo pipefail

# Generated structural verifier. Replace or extend with the real deterministic
# checks for this loop, but do not weaken existing checks without human approval.
{body}
"""


def render_adapters_md(manifest: dict[str, Any]) -> str:
    portability = manifest["portability_policy"]
    rows = []
    for adapter in manifest["execution_adapters"]:
        rows.append(
            "| {target} | {instructions} | {subagents} | {hooks} | {generated} |".format(
                target=adapter["target"],
                instructions=", ".join(adapter["instruction_files"]),
                subagents=str(adapter["supports_subagents"]).lower(),
                hooks=adapter["deterministic_hooks"],
                generated=", ".join(adapter["generated_files"]) or "none",
            )
        )
    return f"""# Agent Runtime Adapters

Canonical manifest: `{portability['canonical_manifest']}`

Adapter outputs are generated artifacts. Do not edit them as the source of truth;
update `loop.json` and regenerate.

Unsupported capability behavior: `{portability['unsupported_capability_behavior']}`

Platform selection query: {portability['platform_selection_query']}

| Target | Instruction Files | Supports Subagents | Hooks | Generated Files |
| --- | --- | --- | --- | --- |
{chr(10).join(rows)}
"""


def render_codex_agents_md(manifest: dict[str, Any]) -> str:
    checklist_path = _checklist_path(manifest)
    progress_path = _progress_path(manifest)
    return f"""# AGENTS.md

This file adapts `{manifest['metadata']['name']}` for Codex.

Canonical loop contract: `loop.json`

## Execution Rules

- Re-read `loop.json`, `state.json`, `{progress_path}`, `{checklist_path}`, `tasks.json`, and `agents.json` before each loop cycle.
- Mark `{checklist_path}` items checked only after their criteria, verifier refs, and evidence refs are satisfied.
- Use subagents only when `collaboration_policy.subagent_activation.allowed_when` applies.
- Do not weaken `verification_policy.protected_paths` or terminal verifier commands.
- Stop and report when a requested capability is unsupported by Codex.
- Gate irreversible actions listed in `human_gates.irreversible_actions`.

## Verification

Run `bash scripts/verify.sh` for terminal verification unless the manifest defines
a stricter runtime-specific verifier.
"""


def render_claude_md(manifest: dict[str, Any]) -> str:
    checklist_path = _checklist_path(manifest)
    progress_path = _progress_path(manifest)
    return f"""# CLAUDE.md

This file adapts `{manifest['metadata']['name']}` for Claude Code.

Canonical loop contract: `loop.json`

## Execution Rules

- Load `loop.json`, `state.json`, `{progress_path}`, `{checklist_path}`, `tasks.json`, and `agents.json` before acting.
- Mark `{checklist_path}` items checked only after their criteria, verifier refs, and evidence refs are satisfied.
- Use Claude Code subagents only when the manifest's subagent activation policy applies.
- Use hooks only to enforce or observe the manifest contract; do not use hooks to bypass verification.
- Stop and ask the user before irreversible actions listed in `human_gates.irreversible_actions`.
- If a manifest capability is unsupported in Claude Code, block and report instead of silently skipping it.
"""


def render_claude_settings_json() -> str:
    settings = {
        "hooks": {
            "PreToolUse": [
                {
                    "matcher": "Bash",
                    "hooks": [
                        {
                            "type": "command",
                            "command": "bash scripts/verify.sh"
                        }
                    ]
                }
            ]
        }
    }
    return _json(settings)


def render_cursor_rule(manifest: dict[str, Any]) -> str:
    checklist_path = _checklist_path(manifest)
    progress_path = _progress_path(manifest)
    return f"""---
description: Looper Creator runtime adapter for {manifest['metadata']['name']}
alwaysApply: false
---

# Looper Creator Cursor Adapter

Canonical loop contract: `loop.json`

- Load `loop.json`, `state.json`, `{progress_path}`, `{checklist_path}`, `tasks.json`, and `agents.json` before each loop cycle.
- Mark `{checklist_path}` items checked only after their criteria, verifier refs, and evidence refs are satisfied.
- Use Cursor subagents or cloud agents only when the manifest's activation policy applies.
- Keep generated adapter files subordinate to `loop.json`.
- Do not weaken verifiers for platform limits.
- If a capability is unsupported in Cursor, block and report rather than silently skipping it.
"""


def render_runtime_json(adapter: dict[str, Any]) -> str:
    return _json(
        {
            "target": adapter["target"],
            "generated_adapter_files": adapter.get("generated_files", []),
            "instruction_files": adapter.get("instruction_files", []),
            "unsupported_capability_behavior": adapter.get("unsupported_capability_behavior"),
        }
    )


def _remove_empty_parents(path: Path, stop: Path) -> None:
    for parent in path.parents:
        if parent == stop:
            break
        try:
            parent.rmdir()
        except OSError:
            break


def cleanup_unselected_adapter_files(manifest: dict[str, Any], output: Path, runtime_target: str) -> None:
    selected = set(_adapter_for_target(manifest, runtime_target).get("generated_files", []))
    stale: set[str] = set()
    for adapter in manifest["execution_adapters"]:
        if adapter.get("target") == runtime_target:
            continue
        for relative in adapter.get("generated_files", []):
            if relative not in selected:
                stale.add(relative)
    for relative in sorted(stale):
        path = output / relative
        if path.is_file() or path.is_symlink():
            path.unlink()
            _remove_empty_parents(path.parent, output)


def generate_adapter_files(manifest: dict[str, Any], output: Path, runtime_target: str) -> None:
    _write(output / "ADAPTERS.md", render_adapters_md(manifest))
    adapter = _adapter_for_target(manifest, runtime_target)
    generated = set(adapter.get("generated_files", []))
    _write(output / "runtime.json", render_runtime_json(adapter))
    if runtime_target == "codex" and "AGENTS.md" in generated:
        _write(output / "AGENTS.md", render_codex_agents_md(manifest))
    if runtime_target == "claude_code":
        if "CLAUDE.md" in generated:
            _write(output / "CLAUDE.md", render_claude_md(manifest))
        if ".claude/settings.json" in generated:
            _write(output / ".claude" / "settings.json", render_claude_settings_json())
    if runtime_target == "cursor" and ".cursor/rules/looper-creator.mdc" in generated:
        _write(output / ".cursor" / "rules" / "looper-creator.mdc", render_cursor_rule(manifest))


def create_project(manifest: dict[str, Any], output: Path, force: bool = False, runtime_target: str = "codex") -> None:
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("manifest validation failed:\n" + "\n".join(f"- {error}" for error in errors))
    _adapter_for_target(manifest, runtime_target)

    if output.exists() and any(output.iterdir()) and not force:
        raise FileExistsError(f"{output} exists and is not empty; pass --force to overwrite generated files")

    state = manifest["state"]
    output.mkdir(parents=True, exist_ok=True)
    cleanup_unselected_adapter_files(manifest, output, runtime_target)
    _write(output / "loop.json", _json(manifest))
    _write(output / "LOOP.md", render_loop_md(manifest))
    _write(output / _checklist_path(manifest), render_acceptance_md(manifest))
    _write(output / state["progress_path"], render_progress_md(manifest))
    _write(output / state["path"], render_state_json(manifest))
    _write(output / state["journal_path"], "")
    _write(output / "loops.json", _json(manifest["loop_nodes"]))
    _write(output / "tasks.json", _json(manifest["atomic_tasks"]))
    _write(output / "agents.json", _json(manifest["agents"]))
    _write(output / "context-policy.json", _json(manifest["context_policy"]))
    (output / manifest["observability"]["evidence_dir"]).mkdir(parents=True, exist_ok=True)
    _write(output / "scripts" / "verify.sh", render_verify_sh(manifest), executable=True)
    generate_adapter_files(manifest, output, runtime_target)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a standard recursive loop project from a manifest.")
    parser.add_argument("--manifest", required=True, help="Path to loop manifest JSON")
    parser.add_argument("--output", help="Output directory. Defaults to manifest metadata.name slug beside the manifest.")
    parser.add_argument("--force", action="store_true", help="Allow writing into an existing non-empty output directory")
    parser.add_argument(
        "--runtime-target",
        choices=["codex", "claude_code", "cursor", "portable"],
        default="codex",
        help="Runtime adapter to generate at the project root. Defaults to codex.",
    )
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    try:
        manifest = load_manifest(manifest_path)
        name = manifest.get("metadata", {}).get("name", "loop-project")
        output = Path(args.output) if args.output else manifest_path.parent / _slug(name)
        create_project(manifest, output, force=args.force, runtime_target=args.runtime_target)
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
