#!/usr/bin/env python3
"""Validate a Looper Creator manifest or generated project."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


TRIGGER_TYPES = {"heartbeat", "cron", "hook", "goal"}
FORBIDDEN_SECRET_KEYS = {
    "password",
    "passwd",
    "token",
    "api_key",
    "apikey",
    "private_key",
    "privatekey",
    "secret",
}
REQUIRED_TOP_LEVEL = {
    "schema_version",
    "name",
    "purpose",
    "trigger",
    "observation",
    "action",
    "success_condition",
    "failure_condition",
    "verifier",
    "budgets",
    "no_progress",
    "state",
    "escalation",
    "human_gates",
}


class ValidationError(Exception):
    """Raised when a manifest or project fails validation."""


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _as_dict(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and value > 0 and not isinstance(value, bool)


def _walk_forbidden_keys(value: Any, path: str, errors: list[str]) -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = key.lower().replace("-", "_")
            if normalized in FORBIDDEN_SECRET_KEYS:
                errors.append(f"{path}.{key} looks like a plaintext secret field")
            _walk_forbidden_keys(child, f"{path}.{key}", errors)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden_keys(child, f"{path}[{index}]", errors)


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL - set(manifest))
    for key in missing:
        errors.append(f"missing required field: {key}")

    _require(manifest.get("schema_version") == "1.0", "schema_version must be '1.0'", errors)
    _require(_non_empty_string(manifest.get("name")), "name must be a non-empty string", errors)
    _require(_non_empty_string(manifest.get("purpose")), "purpose must be a non-empty string", errors)

    trigger = _as_dict(manifest.get("trigger"), "trigger", errors)
    trigger_type = trigger.get("type")
    _require(trigger_type in TRIGGER_TYPES, "trigger.type must be heartbeat, cron, hook, or goal", errors)
    _require(_non_empty_string(trigger.get("description")), "trigger.description must be a non-empty string", errors)
    if trigger_type in {"heartbeat", "cron"}:
        _require(_non_empty_string(trigger.get("schedule")), "heartbeat/cron triggers require trigger.schedule", errors)
    if trigger_type == "hook":
        _require(_non_empty_string(trigger.get("event_source")), "hook triggers require trigger.event_source", errors)
        _require(_non_empty_string(trigger.get("backpressure")), "hook triggers require trigger.backpressure", errors)

    for section_name in ("observation", "action", "success_condition", "failure_condition"):
        section = _as_dict(manifest.get(section_name), section_name, errors)
        _require(_non_empty_string(section.get("description")), f"{section_name}.description must be non-empty", errors)

    success = _as_dict(manifest.get("success_condition"), "success_condition", errors)
    _require(
        _non_empty_string(success.get("check_command")) or _non_empty_string(success.get("evidence")),
        "success_condition requires check_command or evidence",
        errors,
    )

    verifier = _as_dict(manifest.get("verifier"), "verifier", errors)
    command = verifier.get("command")
    _require(_non_empty_string(command), "verifier.command must be a non-empty string", errors)
    if isinstance(command, str):
        unsafe_fragments = ["|| true", "continue-on-error", "set +e"]
        for fragment in unsafe_fragments:
            _require(fragment not in command, f"verifier.command must not contain '{fragment}'", errors)
    _require(_non_empty_string(verifier.get("expected_result")), "verifier.expected_result must be non-empty", errors)
    protected_paths = verifier.get("protected_paths")
    _require(isinstance(protected_paths, list) and bool(protected_paths), "verifier.protected_paths must be a non-empty list", errors)

    budgets = _as_dict(manifest.get("budgets"), "budgets", errors)
    for key in ("max_iterations", "wall_clock_minutes"):
        _require(_positive_int(budgets.get(key)), f"budgets.{key} must be a positive integer", errors)
    if "max_tokens" in budgets:
        _require(_positive_int(budgets.get("max_tokens")), "budgets.max_tokens must be a positive integer", errors)
    if "max_cost_usd" in budgets:
        _require(isinstance(budgets.get("max_cost_usd"), (int, float)) and budgets.get("max_cost_usd") > 0, "budgets.max_cost_usd must be positive", errors)

    no_progress = _as_dict(manifest.get("no_progress"), "no_progress", errors)
    _require(_positive_int(no_progress.get("max_stale_iterations")), "no_progress.max_stale_iterations must be a positive integer", errors)
    fingerprint_fields = no_progress.get("fingerprint_fields")
    _require(
        isinstance(fingerprint_fields, list) and all(_non_empty_string(item) for item in fingerprint_fields) and len(fingerprint_fields) >= 2,
        "no_progress.fingerprint_fields must contain at least two non-empty strings",
        errors,
    )

    state = _as_dict(manifest.get("state"), "state", errors)
    _require(_non_empty_string(state.get("path")), "state.path must be non-empty", errors)
    _require(_non_empty_string(state.get("journal_path")), "state.journal_path must be non-empty", errors)

    escalation = _as_dict(manifest.get("escalation"), "escalation", errors)
    for key in ("condition", "owner", "channel", "message_template"):
        _require(_non_empty_string(escalation.get(key)), f"escalation.{key} must be non-empty", errors)

    human_gates = _as_dict(manifest.get("human_gates"), "human_gates", errors)
    irreversible_actions = human_gates.get("irreversible_actions")
    _require(
        isinstance(irreversible_actions, list) and all(_non_empty_string(item) for item in irreversible_actions),
        "human_gates.irreversible_actions must be a list of strings",
        errors,
    )

    _walk_forbidden_keys(manifest, "$", errors)
    return errors


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValidationError(f"{path}: manifest must be a JSON object")
    return data


def validate_project(path: Path) -> list[str]:
    errors: list[str] = []
    manifest_path = path / "loop.json"
    if not manifest_path.exists():
        return [f"{manifest_path} does not exist"]

    try:
        manifest = load_manifest(manifest_path)
    except ValidationError as exc:
        return [str(exc)]

    errors.extend(validate_manifest(manifest))
    required_files = [
        "LOOP.md",
        "PROGRESS.md",
        "loop.json",
        manifest.get("state", {}).get("path", "state.json"),
        manifest.get("state", {}).get("journal_path", "journal.jsonl"),
        "scripts/verify.sh",
    ]
    for relative in required_files:
        if isinstance(relative, str):
            _require((path / relative).exists(), f"missing generated file: {relative}", errors)

    verify_path = path / "scripts" / "verify.sh"
    if verify_path.exists():
        _require(os.access(verify_path, os.X_OK), "scripts/verify.sh must be executable", errors)
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a Looper Creator manifest or generated project.")
    parser.add_argument("path", help="Path to a loop manifest JSON file or generated project directory")
    args = parser.parse_args(argv)

    path = Path(args.path)
    if not path.exists():
        print(f"ERROR: {path} does not exist", file=sys.stderr)
        return 2

    if path.is_dir():
        errors = validate_project(path)
    else:
        try:
            errors = validate_manifest(load_manifest(path))
        except ValidationError as exc:
            errors = [str(exc)]

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"OK: {path} is a valid Looper Creator artifact")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
