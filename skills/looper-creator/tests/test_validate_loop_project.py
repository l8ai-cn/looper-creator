import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))

from create_loop_project import create_project  # noqa: E402
from validate_loop_project import load_manifest, validate_manifest, validate_project  # noqa: E402


def recursive_manifest():
    return {
        "kind": "RecursiveLoopOrchestration",
        "schema_version": "2.0",
        "metadata": {
            "id": "feature-development-loop",
            "name": "Feature Development Loop",
            "description": "Plan, implement, verify, and review one feature with recursive task decomposition.",
            "locale": "en",
        },
        "objective": {
            "user_goal": "Implement one scoped product feature without weakening tests or deployment checks.",
            "business_value": "Reduce repeated agent context loading while preserving deterministic completion evidence.",
            "done_definition": "All atomic tasks are accepted and terminal verification commands exit 0.",
            "non_goals": ["Do not deploy automatically", "Do not rewrite unrelated modules"],
        },
        "clarification_policy": {
            "ambiguity_triggers": [
                "acceptance criteria missing",
                "target environment unclear",
                "permission boundary unclear",
            ],
            "default_action": "ask_user",
            "secondary_user_query": {
                "prompt": "Which target feature, acceptance criteria, and verification command should this loop use?",
                "required_when": ["acceptance criteria missing", "verification command missing"],
                "max_questions": 3,
            },
            "assumption_policy": {
                "allowed": "Only low-risk implementation details may be assumed.",
                "record_path": "PROGRESS.md",
            },
            "block_if": ["security impact unclear", "production data impact unclear"],
        },
        "decomposition_policy": {
            "strategy": "recursive_task_graph",
            "split_until": [
                "each task has one owner agent",
                "each task has machine-checkable acceptance criteria",
                "each task can fit inside its context token budget",
            ],
            "minimum_task_granularity": "one independently verifiable code, test, docs, or review change",
            "max_depth": 4,
            "dependency_policy": "parents cannot complete until all children and verification refs pass",
        },
        "loop_nodes": [
            {
                "id": "root",
                "type": "agent_loop",
                "purpose": "Coordinate recursive decomposition and terminal verification.",
                "entry_conditions": ["clarification_policy satisfied", "state.status is planned or running"],
                "exit_conditions": ["terminal_verification_passed", "budget_exit_reached", "human_gate_required"],
                "steps": ["load_context", "decompose", "dispatch_children", "verify", "record"],
                "context_pack": ["loop.json", "PROGRESS.md", "state.json"],
                "agent_assignments": ["orchestrator"],
                "verification_refs": ["terminal"],
                "children": [
                    {
                        "id": "implementation-cycle",
                        "type": "evaluator_optimizer_loop",
                        "purpose": "Iterate implementation tasks until per-task verification passes.",
                        "entry_conditions": ["atomic_tasks ready"],
                        "exit_conditions": ["all child tasks accepted", "no_progress_exit"],
                        "steps": ["assign_task", "implement", "self_check", "deterministic_check", "review"],
                        "context_pack": ["task card", "relevant source files", "verifier output"],
                        "agent_assignments": ["worker", "reviewer"],
                        "verification_refs": ["unit-tests"],
                    }
                ],
            }
        ],
        "atomic_tasks": [
            {
                "id": "task-implement",
                "goal": "Implement the scoped feature change.",
                "input_refs": ["requirements.md", "src/"],
                "output_artifacts": ["source diff", "test diff"],
                "dependencies": [],
                "assigned_agent": "worker",
                "tools": ["shell", "apply_patch"],
                "acceptance_criteria": ["unit-tests verifier exits 0", "reviewer accepts diff"],
                "verification_refs": ["unit-tests"],
                "max_attempts": 3,
                "estimated_token_budget": 20000,
            }
        ],
        "agents": [
            {
                "id": "orchestrator",
                "role": "orchestrator",
                "model_class": "strong_reasoning",
                "responsibilities": ["maintain plan", "dispatch tasks", "decide exits"],
                "context_scope": "shared",
                "may_modify": ["PROGRESS.md", "state.json", "tasks.json"],
            },
            {
                "id": "worker",
                "role": "worker",
                "model_class": "fast_worker",
                "responsibilities": ["execute one atomic task"],
                "context_scope": "task_private",
                "may_modify": ["source files", "tests"],
            },
            {
                "id": "reviewer",
                "role": "reviewer",
                "model_class": "strong_reasoning",
                "responsibilities": ["review task output against acceptance criteria"],
                "context_scope": "review_private",
                "may_modify": ["review report"],
            },
        ],
        "collaboration_policy": {
            "patterns": ["orchestrator_workers", "evaluator_optimizer"],
            "subagent_activation": {
                "allowed_when": [
                    "tasks are independent",
                    "context would exceed single-agent budget",
                    "independent review is required",
                ],
                "disallowed_when": ["shared mutable file would be edited by multiple workers"],
                "token_budget_policy": "subagents must return distilled summaries under 2000 tokens",
            },
            "handoff_contract": {
                "required_fields": ["task_id", "context_pack", "expected_output", "verification_refs"],
                "return_fields": ["status", "artifacts", "evidence", "open_questions"],
            },
        },
        "context_policy": {
            "max_context_tokens": 60000,
            "required_context_pack": ["loop.json", "state.json", "PROGRESS.md"],
            "retrieval_strategy": "just_in_time",
            "tool_output_trimming": "include only commands, exit codes, failing assertions, and changed paths",
            "compaction": {
                "trigger_ratio": 0.8,
                "summary_contract": "preserve decisions, open tasks, verification evidence, and risks",
            },
            "durable_memory": {
                "state_path": "state.json",
                "journal_path": "journal.jsonl",
                "progress_path": "PROGRESS.md",
            },
            "excluded_context": ["secrets", "raw tokens", "unrelated logs"],
        },
        "termination_policy": {
            "success": ["terminal verification commands exit 0", "all atomic tasks accepted"],
            "failure": ["required dependency unavailable", "protected verifier must change"],
            "budget_exits": {"max_iterations": 8, "wall_clock_minutes": 90, "max_tokens": 180000},
            "no_progress": {
                "fingerprint_fields": ["git_head", "open_task_ids", "verifier_failures"],
                "max_stale_iterations": 2,
            },
            "human_gate": ["before git push", "before production deploy"],
        },
        "verification_policy": {
            "verifiers": [
                {
                    "id": "unit-tests",
                    "command": "python3 -m unittest discover -s tests",
                    "expected_result": "exit code 0",
                    "scope": "per_task",
                },
                {
                    "id": "terminal",
                    "command": "bash scripts/verify.sh",
                    "expected_result": "exit code 0",
                    "scope": "terminal",
                },
            ],
            "protected_paths": ["scripts/verify.sh", ".github/workflows", "tests"],
            "anti_gaming_rules": [
                "do not delete tests",
                "do not weaken verifier commands",
                "do not add continue-on-error",
            ],
        },
        "cost_policy": {
            "optimization_goal": "minimize repeated context loading while preserving verification evidence",
            "token_budget_by_agent": {"orchestrator": 80000, "worker": 40000, "reviewer": 30000},
            "stop_when_marginal_value_low": True,
        },
        "risk_policy": {
            "risk_levels": ["low", "medium", "high", "critical"],
            "high_risk_requires_human": ["security", "production data", "billing", "deployment"],
            "forbidden_behaviors": ["silent fallback", "weakening validation", "storing plaintext secrets"],
        },
        "execution_adapters": [
            {
                "target": "codex",
                "instruction_files": ["AGENTS.md"],
                "supports_subagents": True,
                "subagent_activation": "explicit_request",
                "deterministic_hooks": "not_assumed",
                "approval_model": "sandbox_and_policy",
                "context_reload_model": "session_instruction_discovery",
                "generated_files": ["AGENTS.md"],
                "unsupported_capability_behavior": "block_and_report",
            },
            {
                "target": "claude_code",
                "instruction_files": ["CLAUDE.md"],
                "supports_subagents": True,
                "subagent_activation": "description_or_explicit_agent",
                "deterministic_hooks": "supported",
                "approval_model": "permissions_and_hooks",
                "context_reload_model": "CLAUDE.md_and_memory",
                "generated_files": ["CLAUDE.md", ".claude/settings.json"],
                "unsupported_capability_behavior": "block_and_report",
            },
            {
                "target": "cursor",
                "instruction_files": ["AGENTS.md", ".cursor/rules/looper-creator.mdc"],
                "supports_subagents": True,
                "subagent_activation": "cursor_subagents_or_cloud_agents",
                "deterministic_hooks": "supported_when_configured",
                "approval_model": "cursor_agent_security",
                "context_reload_model": "rules_skills_mentions",
                "generated_files": [".cursor/rules/looper-creator.mdc"],
                "unsupported_capability_behavior": "block_and_report",
            },
        ],
        "portability_policy": {
            "canonical_manifest": "loop.json",
            "adapter_outputs_are_generated": True,
            "do_not_weaken_verification_for_platform_limits": True,
            "unsupported_capability_behavior": "block_and_report",
            "platform_selection_query": "Which agent runtime should this loop target: codex, claude_code, cursor, or portable?",
        },
        "failure_modes": [
            {"id": "vague-objective", "mitigation": "trigger clarification_policy.secondary_user_query"},
            {"id": "context-bloat", "mitigation": "trim tool outputs and compact at threshold"},
            {"id": "no-progress", "mitigation": "compare fingerprints and stop at threshold"},
        ],
        "templates": ["feature-development", "testing-debugging", "documentation-writing"],
        "acceptance_checklist": {
            "path": "ACCEPTANCE.md",
            "update_policy": "one checklist item must be marked only after its verifier evidence exists",
            "items": [
                {
                    "id": "accept-task-implement",
                    "task_id": "task-implement",
                    "description": "Implementation task is complete and verified.",
                    "owner_agent": "reviewer",
                    "acceptance_criteria": ["unit-tests verifier exits 0", "reviewer accepts diff"],
                    "verification_refs": ["unit-tests"],
                    "evidence_refs": ["source diff", "test diff"],
                }
            ],
        },
        "state": {"path": "state.json", "journal_path": "journal.jsonl", "progress_path": "PROGRESS.md"},
        "observability": {
            "trace_fields": ["loop_node_id", "task_id", "agent_id", "verifier_id", "token_estimate"],
            "evidence_dir": "evidence",
        },
        "human_gates": {
            "irreversible_actions": ["git push", "merge pull request", "deploy to production"],
            "approval_record_path": "PROGRESS.md",
        },
        "escalation": {
            "condition": "budget, no-progress, ambiguity, or human-gate exit is reached",
            "owner": "human maintainer",
            "channel": "Codex thread",
            "message_template": "Loop {metadata.name} stopped: {reason}. Evidence: {evidence_ref}.",
        },
    }


class LooperCreatorValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp(prefix="looper-creator-test-"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_v2_recursive_manifest_and_generated_project(self):
        manifest = recursive_manifest()
        self.assertEqual([], validate_manifest(manifest))
        output = self.tmpdir / "generated"
        create_project(manifest, output)
        self.assertEqual([], validate_project(output))
        for relative in [
            "LOOP.md",
            "PROGRESS.md",
            "ACCEPTANCE.md",
            "loop.json",
            "loops.json",
            "tasks.json",
            "agents.json",
            "context-policy.json",
            "ADAPTERS.md",
            "AGENTS.md",
            "runtime.json",
            "scripts/verify.sh",
        ]:
            self.assertTrue((output / relative).exists(), relative)
        for relative in [
            "CLAUDE.md",
            ".claude/settings.json",
            ".cursor/rules/looper-creator.mdc",
        ]:
            self.assertFalse((output / relative).exists(), relative)
        verifier_script = (output / "scripts" / "verify.sh").read_text(encoding="utf-8")
        self.assertNotIn("python3 -m unittest discover -s tests", verifier_script)

    def test_generated_project_can_select_claude_runtime_adapter(self):
        manifest = recursive_manifest()
        output = self.tmpdir / "generated-claude"
        create_project(manifest, output, runtime_target="claude_code")
        self.assertEqual([], validate_project(output))
        self.assertTrue((output / "CLAUDE.md").exists())
        self.assertTrue((output / ".claude" / "settings.json").exists())
        self.assertFalse((output / "AGENTS.md").exists())
        self.assertFalse((output / ".cursor" / "rules" / "looper-creator.mdc").exists())
        runtime = json.loads((output / "runtime.json").read_text(encoding="utf-8"))
        self.assertEqual("claude_code", runtime["target"])

    def test_generated_claude_hook_does_not_weaken_verification(self):
        manifest = recursive_manifest()
        output = self.tmpdir / "generated-claude-hook"
        create_project(manifest, output, runtime_target="claude_code")
        settings_text = (output / ".claude" / "settings.json").read_text(encoding="utf-8")
        self.assertNotIn("|| true", settings_text)
        self.assertNotIn("continue-on-error", settings_text)
        self.assertNotIn("set +e", settings_text)
        self.assertNotIn("validate_loop_project.py", settings_text)
        self.assertIn("bash scripts/verify.sh", settings_text)

    def test_force_regeneration_removes_stale_unselected_adapter_files(self):
        manifest = recursive_manifest()
        output = self.tmpdir / "generated-force-runtime"
        create_project(manifest, output, runtime_target="codex")
        self.assertTrue((output / "AGENTS.md").exists())

        create_project(manifest, output, force=True, runtime_target="claude_code")

        self.assertEqual([], validate_project(output))
        self.assertFalse((output / "AGENTS.md").exists())
        self.assertTrue((output / "CLAUDE.md").exists())
        self.assertTrue((output / ".claude" / "settings.json").exists())

    def test_v2_requires_clarification_policy_for_ambiguous_requests(self):
        manifest = recursive_manifest()
        del manifest["clarification_policy"]
        errors = validate_manifest(manifest)
        self.assertTrue(any("clarification_policy" in error for error in errors))

    def test_v2_rejects_subagent_activation_without_token_budget_policy(self):
        manifest = recursive_manifest()
        manifest["collaboration_policy"]["subagent_activation"]["token_budget_policy"] = ""
        errors = validate_manifest(manifest)
        self.assertTrue(any("token_budget_policy" in error for error in errors))

    def test_v2_rejects_adapter_silent_degradation(self):
        manifest = recursive_manifest()
        manifest["execution_adapters"][0]["unsupported_capability_behavior"] = "silent_skip"
        manifest["portability_policy"]["unsupported_capability_behavior"] = "silent_skip"
        errors = validate_manifest(manifest)
        self.assertTrue(any("unsupported_capability_behavior" in error for error in errors))

    def test_v2_requires_acceptance_checklist(self):
        manifest = recursive_manifest()
        del manifest["acceptance_checklist"]
        errors = validate_manifest(manifest)
        self.assertTrue(any("acceptance_checklist" in error for error in errors))

    def test_v2_rejects_acceptance_checklist_path_traversal(self):
        manifest = recursive_manifest()
        manifest["acceptance_checklist"]["path"] = "../ACCEPTANCE.md"
        errors = validate_manifest(manifest)
        self.assertTrue(any("acceptance_checklist.path" in error and "relative" in error for error in errors))

    def test_v2_rejects_durable_memory_state_path_mismatch(self):
        manifest = recursive_manifest()
        manifest["context_policy"]["durable_memory"]["progress_path"] = "OTHER_PROGRESS.md"
        errors = validate_manifest(manifest)
        self.assertTrue(any("durable_memory.progress_path must match state.progress_path" in error for error in errors))

    def test_v2_rejects_acceptance_checklist_drift_from_atomic_task(self):
        manifest = recursive_manifest()
        item = manifest["acceptance_checklist"]["items"][0]
        item["acceptance_criteria"] = ["reviewer accepts diff"]
        item["verification_refs"] = ["terminal"]
        item["evidence_refs"] = ["source diff"]
        errors = validate_manifest(manifest)
        self.assertTrue(any("must include atomic task acceptance criterion" in error for error in errors))
        self.assertTrue(any("must include atomic task verifier" in error for error in errors))
        self.assertTrue(any("must include atomic task output artifact" in error for error in errors))

    def test_generated_project_honors_custom_runtime_paths(self):
        manifest = recursive_manifest()
        manifest["state"] = {
            "path": "run/state.json",
            "journal_path": "run/journal.jsonl",
            "progress_path": "run/PROGRESS.md",
        }
        manifest["context_policy"]["durable_memory"] = {
            "state_path": "run/state.json",
            "journal_path": "run/journal.jsonl",
            "progress_path": "run/PROGRESS.md",
        }
        manifest["clarification_policy"]["assumption_policy"]["record_path"] = "run/PROGRESS.md"
        manifest["human_gates"]["approval_record_path"] = "run/PROGRESS.md"
        manifest["acceptance_checklist"]["path"] = "run/ACCEPTANCE.md"
        self.assertEqual([], validate_manifest(manifest))
        output = self.tmpdir / "generated-custom-paths"
        create_project(manifest, output)
        self.assertEqual([], validate_project(output))
        self.assertTrue((output / "run" / "PROGRESS.md").exists())
        self.assertTrue((output / "run" / "ACCEPTANCE.md").exists())
        self.assertFalse((output / "PROGRESS.md").exists())
        self.assertFalse((output / "ACCEPTANCE.md").exists())
        adapter_text = (output / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("run/PROGRESS.md", adapter_text)
        self.assertIn("run/ACCEPTANCE.md", adapter_text)
        acceptance_text = (output / "run" / "ACCEPTANCE.md").read_text(encoding="utf-8")
        self.assertIn("run/PROGRESS.md", acceptance_text)

    def test_generated_project_contains_acceptance_checklist_and_verifier(self):
        manifest = recursive_manifest()
        self.assertEqual([], validate_manifest(manifest))
        output = self.tmpdir / "generated-checklist"
        create_project(manifest, output)
        self.assertEqual([], validate_project(output))
        checklist = output / "ACCEPTANCE.md"
        self.assertTrue(checklist.exists())
        checklist_text = checklist.read_text(encoding="utf-8")
        self.assertIn("- [ ]", checklist_text)
        self.assertIn("accept-task-implement", checklist_text)
        verifier_script = (output / "scripts" / "verify.sh").read_text(encoding="utf-8")
        self.assertIn("ACCEPTANCE.md", verifier_script)

    def test_terminal_verifier_rejects_complete_state_with_unchecked_items(self):
        manifest = recursive_manifest()
        output = self.tmpdir / "generated-incomplete"
        create_project(manifest, output)
        result = subprocess.run(["bash", "scripts/verify.sh"], cwd=output, check=False)
        self.assertEqual(0, result.returncode)

        state_path = output / "state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state["status"] = "complete"
        state_path.write_text(json.dumps(state, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")

        result = subprocess.run(["bash", "scripts/verify.sh"], cwd=output, check=False)
        self.assertNotEqual(0, result.returncode)

    def test_invalid_manifest_is_rejected(self):
        manifest = load_manifest(SKILL_DIR / "examples" / "invalid-vague-goal.loop.json")
        errors = validate_manifest(manifest)
        self.assertTrue(errors)
        self.assertTrue(any("clarification_policy" in error for error in errors))

    def test_all_valid_examples_validate(self):
        for path in sorted((SKILL_DIR / "examples").glob("*.loop.json")):
            if path.name.startswith("invalid-"):
                continue
            with self.subTest(path=path.name):
                manifest = load_manifest(path)
                self.assertEqual([], validate_manifest(manifest))

    def test_plaintext_secret_key_is_rejected(self):
        manifest = recursive_manifest()
        manifest["verification_policy"]["token"] = "not-allowed"
        errors = validate_manifest(manifest)
        self.assertTrue(any("plaintext secret" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
