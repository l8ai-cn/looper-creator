#!/usr/bin/env python3
"""Create a standard loop project from a Looper Creator manifest."""

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


def render_loop_md(manifest: dict[str, Any]) -> str:
    trigger = manifest["trigger"]
    budgets = manifest["budgets"]
    no_progress = manifest["no_progress"]
    state = manifest["state"]
    escalation = manifest["escalation"]
    human_gates = manifest["human_gates"]
    protected = "\n".join(f"- `{item}`" for item in manifest["verifier"]["protected_paths"])
    gates = "\n".join(f"- {item}" for item in human_gates["irreversible_actions"]) or "- None"
    fingerprints = ", ".join(f"`{item}`" for item in no_progress["fingerprint_fields"])

    return f"""# {manifest['name']}

## Purpose

{manifest['purpose']}

## Trigger

- Type: `{trigger['type']}`
- Description: {trigger['description']}
- Schedule: {trigger.get('schedule', 'n/a')}
- Event source: {trigger.get('event_source', 'n/a')}
- Backpressure: {trigger.get('backpressure', 'n/a')}

## Cycle Contract

1. Observe: {manifest['observation']['description']}
2. Act: {manifest['action']['description']}
3. Verify: run `{manifest['verifier']['command']}`
4. Record: update `{state['path']}` and append to `{state['journal_path']}`.

## Success

{manifest['success_condition']['description']}

Check: `{manifest['success_condition'].get('check_command', manifest['success_condition'].get('evidence', 'n/a'))}`

## Failure

{manifest['failure_condition']['description']}

## Guardrails

- Max iterations: {budgets['max_iterations']}
- Wall-clock minutes: {budgets['wall_clock_minutes']}
- Max tokens: {budgets.get('max_tokens', 'n/a')}
- Max cost USD: {budgets.get('max_cost_usd', 'n/a')}
- No-progress threshold: {no_progress['max_stale_iterations']} stale iterations
- Fingerprint fields: {fingerprints}

## Verification Integrity

Expected verifier result: {manifest['verifier']['expected_result']}

Protected paths:

{protected}

The loop controller must reject changes that weaken these verifier paths unless a
human explicitly approves the verifier change.

## Human Gates

Stop for approval before:

{gates}

## Escalation

- Condition: {escalation['condition']}
- Owner: {escalation['owner']}
- Channel: {escalation['channel']}
- Message template: {escalation['message_template']}
"""


def render_progress_md(manifest: dict[str, Any]) -> str:
    return f"""# Progress

Loop: {manifest['name']}

## Current Status

- Status: planned
- Current iteration: 0
- Last verifier result: not run
- Last no-progress fingerprint: not recorded

## Decisions

- Initial loop contract generated from `loop.json`.

## Next Cycle

1. Re-read `loop.json`, `state.json`, and this file.
2. Run one observe-act-verify-record cycle.
3. Stop if success, failure, budget, no-progress, or human-gate conditions are met.
"""


def render_state_json(manifest: dict[str, Any]) -> str:
    state = {
        "schema_version": "1.0",
        "loop_name": manifest["name"],
        "status": "planned",
        "iteration": 0,
        "started_at": None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "last_verifier_exit_code": None,
        "last_no_progress_fingerprint": None,
        "stale_iterations": 0,
        "terminal_reason": None,
    }
    return json.dumps(state, indent=2, sort_keys=True) + "\n"


def render_verify_sh(manifest: dict[str, Any]) -> str:
    command = manifest["success_condition"].get("check_command") or manifest["verifier"]["command"]
    return f"""#!/usr/bin/env bash
set -euo pipefail

# Replace this placeholder with the real deterministic verifier for this loop.
# The command below comes from loop.json and must remain stricter than the loop's
# success condition, not easier to satisfy.
{command}
"""


def create_project(manifest: dict[str, Any], output: Path, force: bool = False) -> None:
    errors = validate_manifest(manifest)
    if errors:
        raise ValueError("manifest validation failed:\n" + "\n".join(f"- {error}" for error in errors))

    if output.exists() and any(output.iterdir()) and not force:
        raise FileExistsError(f"{output} exists and is not empty; pass --force to overwrite generated files")

    output.mkdir(parents=True, exist_ok=True)
    _write(output / "loop.json", json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    _write(output / "LOOP.md", render_loop_md(manifest))
    _write(output / "PROGRESS.md", render_progress_md(manifest))
    _write(output / manifest["state"]["path"], render_state_json(manifest))
    _write(output / manifest["state"]["journal_path"], "")
    _write(output / "scripts" / "verify.sh", render_verify_sh(manifest), executable=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create a standard loop project from a manifest.")
    parser.add_argument("--manifest", required=True, help="Path to loop manifest JSON")
    parser.add_argument("--output", help="Output directory. Defaults to manifest name slug beside the manifest.")
    parser.add_argument("--force", action="store_true", help="Allow writing into an existing non-empty output directory")
    args = parser.parse_args(argv)

    manifest_path = Path(args.manifest)
    try:
        manifest = load_manifest(manifest_path)
        output = Path(args.output) if args.output else manifest_path.parent / _slug(manifest.get("name", "loop-project"))
        create_project(manifest, output, force=args.force)
        errors = validate_project(output)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: created loop project at {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
