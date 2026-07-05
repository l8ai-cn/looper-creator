#!/usr/bin/env python3
"""Validate a Looper Creator recursive loop manifest or generated project."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any


KIND = "RecursiveLoopOrchestration"
SCHEMA_VERSION = "2.0"
LOOP_NODE_TYPES = {
    "workflow",
    "agent_loop",
    "reflection_loop",
    "evaluator_optimizer_loop",
    "parallel_section",
    "handoff_loop",
    "human_review_gate",
}
CLARIFICATION_ACTIONS = {"ask_user", "make_low_risk_assumption", "generate_options", "block_until_answer"}
ADAPTER_TARGETS = {"codex", "claude_code", "cursor", "portable"}
UNSUPPORTED_CAPABILITY_BEHAVIOR = "block_and_report"
UNSAFE_COMMAND_FRAGMENTS = ("|| true", "continue-on-error", "set +e")
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
    "kind",
    "schema_version",
    "metadata",
    "objective",
    "clarification_policy",
    "decomposition_policy",
    "loop_nodes",
    "atomic_tasks",
    "agents",
    "collaboration_policy",
    "context_policy",
    "termination_policy",
    "verification_policy",
    "cost_policy",
    "risk_policy",
    "execution_adapters",
    "portability_policy",
    "failure_modes",
    "templates",
    "acceptance_checklist",
    "state",
    "observability",
    "human_gates",
    "escalation",
}


class ValidationError(Exception):
    """Raised when a manifest or project cannot be loaded."""


def _require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def _as_dict(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def _as_list(value: Any, name: str, errors: list[str], min_items: int = 1) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{name} must be a list")
        return []
    if len(value) < min_items:
        errors.append(f"{name} must contain at least {min_items} item(s)")
    return value


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and value > 0 and not isinstance(value, bool)


def _positive_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and value > 0 and not isinstance(value, bool)


def _safe_project_path(value: str) -> bool:
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def _validate_project_path(value: Any, name: str, errors: list[str]) -> None:
    _require(_non_empty_string(value), f"{name} must be non-empty", errors)
    if isinstance(value, str) and value.strip():
        _require(_safe_project_path(value), f"{name} must be relative and must not contain '..'", errors)


def _string_list(value: Any, name: str, errors: list[str], min_items: int = 1) -> list[str]:
    items = _as_list(value, name, errors, min_items=min_items)
    if not all(_non_empty_string(item) for item in items):
        errors.append(f"{name} must contain only non-empty strings")
        return []
    return items


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


def _validate_command(command: Any, path: str, errors: list[str]) -> None:
    _require(_non_empty_string(command), f"{path} must be a non-empty string", errors)
    if isinstance(command, str):
        for fragment in UNSAFE_COMMAND_FRAGMENTS:
            _require(fragment not in command, f"{path} must not contain '{fragment}'", errors)


def _validate_metadata(manifest: dict[str, Any], errors: list[str]) -> None:
    metadata = _as_dict(manifest.get("metadata"), "metadata", errors)
    for key in ("id", "name", "description", "locale"):
        _require(_non_empty_string(metadata.get(key)), f"metadata.{key} must be non-empty", errors)


def _validate_objective(manifest: dict[str, Any], errors: list[str]) -> None:
    objective = _as_dict(manifest.get("objective"), "objective", errors)
    for key in ("user_goal", "done_definition"):
        _require(_non_empty_string(objective.get(key)), f"objective.{key} must be non-empty", errors)
    _string_list(objective.get("non_goals"), "objective.non_goals", errors, min_items=0)


def _validate_clarification_policy(manifest: dict[str, Any], errors: list[str]) -> None:
    policy = _as_dict(manifest.get("clarification_policy"), "clarification_policy", errors)
    _string_list(policy.get("ambiguity_triggers"), "clarification_policy.ambiguity_triggers", errors)
    _require(
        policy.get("default_action") in CLARIFICATION_ACTIONS,
        "clarification_policy.default_action must be ask_user, make_low_risk_assumption, generate_options, or block_until_answer",
        errors,
    )
    secondary = _as_dict(policy.get("secondary_user_query"), "clarification_policy.secondary_user_query", errors)
    _require(_non_empty_string(secondary.get("prompt")), "clarification_policy.secondary_user_query.prompt must be non-empty", errors)
    _string_list(secondary.get("required_when"), "clarification_policy.secondary_user_query.required_when", errors)
    _require(_positive_int(secondary.get("max_questions")), "clarification_policy.secondary_user_query.max_questions must be a positive integer", errors)
    assumption = _as_dict(policy.get("assumption_policy"), "clarification_policy.assumption_policy", errors)
    _require(_non_empty_string(assumption.get("allowed")), "clarification_policy.assumption_policy.allowed must be non-empty", errors)
    _validate_project_path(assumption.get("record_path"), "clarification_policy.assumption_policy.record_path", errors)
    _string_list(policy.get("block_if"), "clarification_policy.block_if", errors)


def _validate_decomposition_policy(manifest: dict[str, Any], errors: list[str]) -> int:
    policy = _as_dict(manifest.get("decomposition_policy"), "decomposition_policy", errors)
    for key in ("strategy", "minimum_task_granularity", "dependency_policy"):
        _require(_non_empty_string(policy.get(key)), f"decomposition_policy.{key} must be non-empty", errors)
    _string_list(policy.get("split_until"), "decomposition_policy.split_until", errors)
    _require(_positive_int(policy.get("max_depth")), "decomposition_policy.max_depth must be a positive integer", errors)
    return policy.get("max_depth") if _positive_int(policy.get("max_depth")) else 1


def _collect_loop_nodes(nodes: list[Any], errors: list[str], path: str, depth: int, max_depth: int) -> set[str]:
    ids: set[str] = set()
    for index, raw_node in enumerate(nodes):
        node_path = f"{path}[{index}]"
        node = _as_dict(raw_node, node_path, errors)
        node_id = node.get("id")
        _require(_non_empty_string(node_id), f"{node_path}.id must be non-empty", errors)
        if _non_empty_string(node_id):
            _require(node_id not in ids, f"{node_path}.id duplicates another loop node id", errors)
            ids.add(node_id)
        _require(node.get("type") in LOOP_NODE_TYPES, f"{node_path}.type must be a known loop node type", errors)
        _require(_non_empty_string(node.get("purpose")), f"{node_path}.purpose must be non-empty", errors)
        _string_list(node.get("entry_conditions"), f"{node_path}.entry_conditions", errors)
        _string_list(node.get("exit_conditions"), f"{node_path}.exit_conditions", errors)
        _string_list(node.get("steps"), f"{node_path}.steps", errors)
        _string_list(node.get("context_pack"), f"{node_path}.context_pack", errors)
        _string_list(node.get("agent_assignments"), f"{node_path}.agent_assignments", errors)
        _string_list(node.get("verification_refs"), f"{node_path}.verification_refs", errors)
        children = node.get("children", [])
        if children:
            _require(depth < max_depth, f"{node_path}.children exceeds decomposition_policy.max_depth", errors)
            child_nodes = _as_list(children, f"{node_path}.children", errors)
            ids.update(_collect_loop_nodes(child_nodes, errors, f"{node_path}.children", depth + 1, max_depth))
    return ids


def _validate_acceptance_checklist(
    manifest: dict[str, Any],
    errors: list[str],
    task_ids: set[str],
    loop_node_ids: set[str],
    agent_ids: set[str],
    verifier_ids: set[str],
) -> None:
    checklist = _as_dict(manifest.get("acceptance_checklist"), "acceptance_checklist", errors)
    _validate_project_path(checklist.get("path"), "acceptance_checklist.path", errors)
    _require(_non_empty_string(checklist.get("update_policy")), "acceptance_checklist.update_policy must be non-empty", errors)
    item_ids: set[str] = set()
    covered_tasks: set[str] = set()
    for index, raw_item in enumerate(_as_list(checklist.get("items"), "acceptance_checklist.items", errors)):
        path = f"acceptance_checklist.items[{index}]"
        item = _as_dict(raw_item, path, errors)
        item_id = item.get("id")
        _require(_non_empty_string(item_id), f"{path}.id must be non-empty", errors)
        if _non_empty_string(item_id):
            _require(item_id not in item_ids, f"{path}.id duplicates another acceptance checklist item id", errors)
            item_ids.add(item_id)
        for key in ("description", "owner_agent"):
            _require(_non_empty_string(item.get(key)), f"{path}.{key} must be non-empty", errors)
        task_id = item.get("task_id")
        loop_node_id = item.get("loop_node_id")
        _require(
            _non_empty_string(task_id) or _non_empty_string(loop_node_id),
            f"{path} must reference task_id or loop_node_id",
            errors,
        )
        if _non_empty_string(task_id):
            _require(task_id in task_ids, f"{path}.task_id must reference an atomic task id", errors)
            covered_tasks.add(task_id)
        if _non_empty_string(loop_node_id):
            _require(loop_node_id in loop_node_ids, f"{path}.loop_node_id must reference a loop node id", errors)
        if _non_empty_string(item.get("owner_agent")):
            _require(item["owner_agent"] in agent_ids, f"{path}.owner_agent must reference an agent id", errors)
        _string_list(item.get("acceptance_criteria"), f"{path}.acceptance_criteria", errors)
        refs = _string_list(item.get("verification_refs"), f"{path}.verification_refs", errors)
        _string_list(item.get("evidence_refs"), f"{path}.evidence_refs", errors)
        for ref in refs:
            _require(ref in verifier_ids, f"{path}.verification_refs contains unknown verifier id: {ref}", errors)
    missing_tasks = sorted(task_ids - covered_tasks)
    for task_id in missing_tasks:
        errors.append(f"acceptance_checklist.items must include a task_id item for atomic task: {task_id}")


def _validate_atomic_tasks(manifest: dict[str, Any], errors: list[str], agent_ids: set[str], verifier_ids: set[str]) -> set[str]:
    task_ids: set[str] = set()
    for index, raw_task in enumerate(_as_list(manifest.get("atomic_tasks"), "atomic_tasks", errors)):
        path = f"atomic_tasks[{index}]"
        task = _as_dict(raw_task, path, errors)
        task_id = task.get("id")
        _require(_non_empty_string(task_id), f"{path}.id must be non-empty", errors)
        if _non_empty_string(task_id):
            _require(task_id not in task_ids, f"{path}.id duplicates another atomic task id", errors)
            task_ids.add(task_id)
        for key in ("goal", "assigned_agent"):
            _require(_non_empty_string(task.get(key)), f"{path}.{key} must be non-empty", errors)
        _string_list(task.get("input_refs"), f"{path}.input_refs", errors)
        _string_list(task.get("output_artifacts"), f"{path}.output_artifacts", errors)
        _string_list(task.get("dependencies"), f"{path}.dependencies", errors, min_items=0)
        _string_list(task.get("tools"), f"{path}.tools", errors, min_items=0)
        _string_list(task.get("acceptance_criteria"), f"{path}.acceptance_criteria", errors)
        refs = _string_list(task.get("verification_refs"), f"{path}.verification_refs", errors)
        _require(_positive_int(task.get("max_attempts")), f"{path}.max_attempts must be a positive integer", errors)
        _require(_positive_int(task.get("estimated_token_budget")), f"{path}.estimated_token_budget must be a positive integer", errors)
        if _non_empty_string(task.get("assigned_agent")):
            _require(task["assigned_agent"] in agent_ids, f"{path}.assigned_agent must reference an agent id", errors)
        for ref in refs:
            _require(ref in verifier_ids, f"{path}.verification_refs contains unknown verifier id: {ref}", errors)
    return task_ids


def _validate_agents(manifest: dict[str, Any], errors: list[str]) -> set[str]:
    agent_ids: set[str] = set()
    for index, raw_agent in enumerate(_as_list(manifest.get("agents"), "agents", errors)):
        path = f"agents[{index}]"
        agent = _as_dict(raw_agent, path, errors)
        agent_id = agent.get("id")
        _require(_non_empty_string(agent_id), f"{path}.id must be non-empty", errors)
        if _non_empty_string(agent_id):
            _require(agent_id not in agent_ids, f"{path}.id duplicates another agent id", errors)
            agent_ids.add(agent_id)
        for key in ("role", "model_class", "context_scope"):
            _require(_non_empty_string(agent.get(key)), f"{path}.{key} must be non-empty", errors)
        _string_list(agent.get("responsibilities"), f"{path}.responsibilities", errors)
        _string_list(agent.get("may_modify"), f"{path}.may_modify", errors, min_items=0)
    return agent_ids


def _validate_collaboration_policy(manifest: dict[str, Any], errors: list[str]) -> None:
    policy = _as_dict(manifest.get("collaboration_policy"), "collaboration_policy", errors)
    _string_list(policy.get("patterns"), "collaboration_policy.patterns", errors)
    activation = _as_dict(policy.get("subagent_activation"), "collaboration_policy.subagent_activation", errors)
    _string_list(activation.get("allowed_when"), "collaboration_policy.subagent_activation.allowed_when", errors)
    _string_list(activation.get("disallowed_when"), "collaboration_policy.subagent_activation.disallowed_when", errors)
    _require(
        _non_empty_string(activation.get("token_budget_policy")),
        "collaboration_policy.subagent_activation.token_budget_policy must be non-empty",
        errors,
    )
    handoff = _as_dict(policy.get("handoff_contract"), "collaboration_policy.handoff_contract", errors)
    _string_list(handoff.get("required_fields"), "collaboration_policy.handoff_contract.required_fields", errors)
    _string_list(handoff.get("return_fields"), "collaboration_policy.handoff_contract.return_fields", errors)


def _validate_context_policy(manifest: dict[str, Any], errors: list[str]) -> None:
    policy = _as_dict(manifest.get("context_policy"), "context_policy", errors)
    _require(_positive_int(policy.get("max_context_tokens")), "context_policy.max_context_tokens must be a positive integer", errors)
    _string_list(policy.get("required_context_pack"), "context_policy.required_context_pack", errors)
    for key in ("retrieval_strategy", "tool_output_trimming"):
        _require(_non_empty_string(policy.get(key)), f"context_policy.{key} must be non-empty", errors)
    compaction = _as_dict(policy.get("compaction"), "context_policy.compaction", errors)
    _require(
        _positive_number(compaction.get("trigger_ratio")) and compaction.get("trigger_ratio") <= 1,
        "context_policy.compaction.trigger_ratio must be a number between 0 and 1",
        errors,
    )
    _require(_non_empty_string(compaction.get("summary_contract")), "context_policy.compaction.summary_contract must be non-empty", errors)
    durable = _as_dict(policy.get("durable_memory"), "context_policy.durable_memory", errors)
    for key in ("state_path", "journal_path", "progress_path"):
        _validate_project_path(durable.get(key), f"context_policy.durable_memory.{key}", errors)
    _string_list(policy.get("excluded_context"), "context_policy.excluded_context", errors)


def _validate_termination_policy(manifest: dict[str, Any], errors: list[str]) -> None:
    policy = _as_dict(manifest.get("termination_policy"), "termination_policy", errors)
    _string_list(policy.get("success"), "termination_policy.success", errors)
    _string_list(policy.get("failure"), "termination_policy.failure", errors)
    _string_list(policy.get("human_gate"), "termination_policy.human_gate", errors)
    budgets = _as_dict(policy.get("budget_exits"), "termination_policy.budget_exits", errors)
    for key in ("max_iterations", "wall_clock_minutes", "max_tokens"):
        _require(_positive_int(budgets.get(key)), f"termination_policy.budget_exits.{key} must be a positive integer", errors)
    no_progress = _as_dict(policy.get("no_progress"), "termination_policy.no_progress", errors)
    _string_list(no_progress.get("fingerprint_fields"), "termination_policy.no_progress.fingerprint_fields", errors, min_items=2)
    _require(_positive_int(no_progress.get("max_stale_iterations")), "termination_policy.no_progress.max_stale_iterations must be a positive integer", errors)


def _validate_verification_policy(manifest: dict[str, Any], errors: list[str]) -> set[str]:
    policy = _as_dict(manifest.get("verification_policy"), "verification_policy", errors)
    verifier_ids: set[str] = set()
    for index, raw_verifier in enumerate(_as_list(policy.get("verifiers"), "verification_policy.verifiers", errors)):
        path = f"verification_policy.verifiers[{index}]"
        verifier = _as_dict(raw_verifier, path, errors)
        verifier_id = verifier.get("id")
        _require(_non_empty_string(verifier_id), f"{path}.id must be non-empty", errors)
        if _non_empty_string(verifier_id):
            _require(verifier_id not in verifier_ids, f"{path}.id duplicates another verifier id", errors)
            verifier_ids.add(verifier_id)
        _validate_command(verifier.get("command"), f"{path}.command", errors)
        for key in ("expected_result", "scope"):
            _require(_non_empty_string(verifier.get(key)), f"{path}.{key} must be non-empty", errors)
    _string_list(policy.get("protected_paths"), "verification_policy.protected_paths", errors)
    rules = _string_list(policy.get("anti_gaming_rules"), "verification_policy.anti_gaming_rules", errors)
    _require(any("weaken" in rule.lower() for rule in rules), "verification_policy.anti_gaming_rules must forbid weakening validation", errors)
    return verifier_ids


def _validate_cost_policy(manifest: dict[str, Any], errors: list[str], agent_ids: set[str]) -> None:
    policy = _as_dict(manifest.get("cost_policy"), "cost_policy", errors)
    _require(_non_empty_string(policy.get("optimization_goal")), "cost_policy.optimization_goal must be non-empty", errors)
    budgets = _as_dict(policy.get("token_budget_by_agent"), "cost_policy.token_budget_by_agent", errors)
    for agent_id in agent_ids:
        _require(_positive_int(budgets.get(agent_id)), f"cost_policy.token_budget_by_agent.{agent_id} must be a positive integer", errors)
    _require(isinstance(policy.get("stop_when_marginal_value_low"), bool), "cost_policy.stop_when_marginal_value_low must be boolean", errors)


def _validate_risk_policy(manifest: dict[str, Any], errors: list[str]) -> None:
    policy = _as_dict(manifest.get("risk_policy"), "risk_policy", errors)
    _string_list(policy.get("risk_levels"), "risk_policy.risk_levels", errors)
    _string_list(policy.get("high_risk_requires_human"), "risk_policy.high_risk_requires_human", errors)
    forbidden = _string_list(policy.get("forbidden_behaviors"), "risk_policy.forbidden_behaviors", errors)
    _require(any("silent fallback" in item.lower() for item in forbidden), "risk_policy.forbidden_behaviors must forbid silent fallback", errors)


def _validate_execution_adapters(manifest: dict[str, Any], errors: list[str]) -> None:
    seen_targets: set[str] = set()
    adapters = _as_list(manifest.get("execution_adapters"), "execution_adapters", errors)
    for index, raw_adapter in enumerate(adapters):
        path = f"execution_adapters[{index}]"
        adapter = _as_dict(raw_adapter, path, errors)
        target = adapter.get("target")
        _require(target in ADAPTER_TARGETS, f"{path}.target must be codex, claude_code, cursor, or portable", errors)
        if target in ADAPTER_TARGETS:
            _require(target not in seen_targets, f"{path}.target duplicates another adapter target", errors)
            seen_targets.add(target)
        _string_list(adapter.get("instruction_files"), f"{path}.instruction_files", errors)
        _require(isinstance(adapter.get("supports_subagents"), bool), f"{path}.supports_subagents must be boolean", errors)
        for key in ("subagent_activation", "deterministic_hooks", "approval_model", "context_reload_model"):
            _require(_non_empty_string(adapter.get(key)), f"{path}.{key} must be non-empty", errors)
        generated_files = _string_list(adapter.get("generated_files"), f"{path}.generated_files", errors, min_items=0)
        for relative in generated_files:
            _validate_project_path(relative, f"{path}.generated_files[]", errors)
        _require(
            adapter.get("unsupported_capability_behavior") == UNSUPPORTED_CAPABILITY_BEHAVIOR,
            f"{path}.unsupported_capability_behavior must be '{UNSUPPORTED_CAPABILITY_BEHAVIOR}'",
            errors,
        )


def _validate_portability_policy(manifest: dict[str, Any], errors: list[str]) -> None:
    policy = _as_dict(manifest.get("portability_policy"), "portability_policy", errors)
    _require(policy.get("canonical_manifest") == "loop.json", "portability_policy.canonical_manifest must be 'loop.json'", errors)
    _require(
        policy.get("adapter_outputs_are_generated") is True,
        "portability_policy.adapter_outputs_are_generated must be true",
        errors,
    )
    _require(
        policy.get("do_not_weaken_verification_for_platform_limits") is True,
        "portability_policy.do_not_weaken_verification_for_platform_limits must be true",
        errors,
    )
    _require(
        policy.get("unsupported_capability_behavior") == UNSUPPORTED_CAPABILITY_BEHAVIOR,
        f"portability_policy.unsupported_capability_behavior must be '{UNSUPPORTED_CAPABILITY_BEHAVIOR}'",
        errors,
    )
    _require(
        _non_empty_string(policy.get("platform_selection_query")),
        "portability_policy.platform_selection_query must be non-empty",
        errors,
    )


def _validate_failure_modes(manifest: dict[str, Any], errors: list[str]) -> None:
    for index, raw_mode in enumerate(_as_list(manifest.get("failure_modes"), "failure_modes", errors)):
        path = f"failure_modes[{index}]"
        mode = _as_dict(raw_mode, path, errors)
        for key in ("id", "mitigation"):
            _require(_non_empty_string(mode.get(key)), f"{path}.{key} must be non-empty", errors)


def _validate_state_and_outputs(manifest: dict[str, Any], errors: list[str]) -> None:
    state = _as_dict(manifest.get("state"), "state", errors)
    for key in ("path", "journal_path", "progress_path"):
        _validate_project_path(state.get(key), f"state.{key}", errors)
    observability = _as_dict(manifest.get("observability"), "observability", errors)
    _string_list(observability.get("trace_fields"), "observability.trace_fields", errors)
    _validate_project_path(observability.get("evidence_dir"), "observability.evidence_dir", errors)
    gates = _as_dict(manifest.get("human_gates"), "human_gates", errors)
    _string_list(gates.get("irreversible_actions"), "human_gates.irreversible_actions", errors, min_items=0)
    _validate_project_path(gates.get("approval_record_path"), "human_gates.approval_record_path", errors)
    escalation = _as_dict(manifest.get("escalation"), "escalation", errors)
    for key in ("condition", "owner", "channel", "message_template"):
        _require(_non_empty_string(escalation.get(key)), f"escalation.{key} must be non-empty", errors)


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_TOP_LEVEL - set(manifest))
    for key in missing:
        errors.append(f"missing required field: {key}")

    _require(manifest.get("kind") == KIND, f"kind must be '{KIND}'", errors)
    _require(manifest.get("schema_version") == SCHEMA_VERSION, f"schema_version must be '{SCHEMA_VERSION}'", errors)
    _walk_forbidden_keys(manifest, "$", errors)

    _validate_metadata(manifest, errors)
    _validate_objective(manifest, errors)
    _validate_clarification_policy(manifest, errors)
    max_depth = _validate_decomposition_policy(manifest, errors)
    agent_ids = _validate_agents(manifest, errors)
    verifier_ids = _validate_verification_policy(manifest, errors)

    loop_nodes = _as_list(manifest.get("loop_nodes"), "loop_nodes", errors)
    loop_node_ids = _collect_loop_nodes(loop_nodes, errors, "loop_nodes", depth=1, max_depth=max_depth)

    for index, raw_node in enumerate(loop_nodes):
        _validate_loop_node_references(raw_node, f"loop_nodes[{index}]", errors, agent_ids, verifier_ids)

    task_ids = _validate_atomic_tasks(manifest, errors, agent_ids, verifier_ids)
    _validate_acceptance_checklist(manifest, errors, task_ids, loop_node_ids, agent_ids, verifier_ids)
    _validate_collaboration_policy(manifest, errors)
    _validate_context_policy(manifest, errors)
    _validate_termination_policy(manifest, errors)
    _validate_cost_policy(manifest, errors, agent_ids)
    _validate_risk_policy(manifest, errors)
    _validate_execution_adapters(manifest, errors)
    _validate_portability_policy(manifest, errors)
    _validate_failure_modes(manifest, errors)
    _string_list(manifest.get("templates"), "templates", errors)
    _validate_state_and_outputs(manifest, errors)
    return errors


def _validate_loop_node_references(
    raw_node: Any,
    path: str,
    errors: list[str],
    agent_ids: set[str],
    verifier_ids: set[str],
) -> None:
    node = _as_dict(raw_node, path, errors)
    for agent_id in node.get("agent_assignments", []):
        _require(agent_id in agent_ids, f"{path}.agent_assignments contains unknown agent id: {agent_id}", errors)
    for verifier_id in node.get("verification_refs", []):
        _require(verifier_id in verifier_ids, f"{path}.verification_refs contains unknown verifier id: {verifier_id}", errors)
    for index, child in enumerate(node.get("children", [])):
        _validate_loop_node_references(child, f"{path}.children[{index}]", errors, agent_ids, verifier_ids)


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
    state = manifest.get("state", {}) if isinstance(manifest.get("state"), dict) else {}
    required_files = [
        "LOOP.md",
        "PROGRESS.md",
        "loop.json",
        "loops.json",
        "tasks.json",
        "agents.json",
        "context-policy.json",
        "ADAPTERS.md",
        state.get("path", "state.json"),
        state.get("journal_path", "journal.jsonl"),
        state.get("progress_path", "PROGRESS.md"),
        "scripts/verify.sh",
    ]
    checklist = manifest.get("acceptance_checklist", {}) if isinstance(manifest.get("acceptance_checklist"), dict) else {}
    if isinstance(checklist.get("path"), str):
        required_files.append(checklist["path"])
    for relative in required_files:
        if isinstance(relative, str):
            _require((path / relative).exists(), f"missing generated file: {relative}", errors)

    for adapter in manifest.get("execution_adapters", []):
        if isinstance(adapter, dict):
            for relative in adapter.get("generated_files", []):
                if isinstance(relative, str):
                    _require((path / relative).exists(), f"missing adapter generated file: {relative}", errors)

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
