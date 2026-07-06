# Awesome Loop Engineering

> Curated learning resources, references, and GitHub projects for building
> agent loops that can run, stop, recover, and stay aligned.
>
> 面向 Loop Engineering / Agent Loop 的精选学习资料、参考知识库和 GitHub
> 项目，关注可持续执行、停止条件、受阻恢复、上下文管理、验证与监督。

[![Awesome](https://awesome.re/badge.svg)](https://awesome.re)

## Purpose / 目的

Loop engineering is the engineering layer around autonomous or semi-autonomous
agents: triggers, state, context, verification, guardrails, human review,
blocked-state recovery, and supervision. This list records the sources and
projects that informed Looper Creator's schema and templates.

Loop Engineering 不是“写一个更长的 prompt”，而是围绕自主或半自主 agent
建立触发、状态、上下文、验证、门禁、人工确认、受阻恢复和监督巡检机制。
本列表记录 Looper Creator schema 与模板设计参考过的资料和项目。

There are already public Awesome-style loop engineering projects. This document
does not try to replace them; it is a project-local learning map and source
ledger for Looper Creator.

公开社区中已经存在 Awesome 风格的 Loop Engineering 项目。本文件不替代它们，
而是作为 Looper Creator 自己的学习地图与设计来源账本。

## Curation Criteria / 筛选标准

- Prefer primary sources, official docs, maintained GitHub projects, and courses
  with concrete implementation patterns.
- Prefer resources that explain loops, workflows, agents, guardrails, state,
  supervision, or human-in-the-loop execution.
- Do not include a resource only because it is popular; include it when it
  changes how a loop should be designed or verified.

- 优先收录一手资料、官方文档、仍在维护的 GitHub 项目，以及包含可执行模式的课程。
- 优先收录解释 loop、workflow、agent、guardrail、state、监督、人工确认的资料。
- 不做资源堆砌；只有能影响 loop 设计、验证或执行控制的内容才进入列表。

This follows the spirit of the [Awesome manifesto](https://github.com/sindresorhus/awesome/blob/main/awesome.md):
curate selectively rather than collecting everything.

## Table of Contents / 目录

- [Existing Awesome Lists / 已有 Awesome 列表](#existing-awesome-lists--已有-awesome-列表)
- [Core Papers, Guides, and Articles / 核心指南与文章](#core-papers-guides-and-articles--核心指南与文章)
- [Courses and Learning Paths / 课程与学习路径](#courses-and-learning-paths--课程与学习路径)
- [GitHub Projects and Frameworks / GitHub 项目与框架](#github-projects-and-frameworks--github-项目与框架)
- [Runtime and Instruction Standards / 运行时与指令标准](#runtime-and-instruction-standards--运行时与指令标准)
- [How Looper Creator Uses These Ideas / Looper Creator 如何吸收这些思想](#how-looper-creator-uses-these-ideas--looper-creator-如何吸收这些思想)
- [Contribution Rules / 贡献规则](#contribution-rules--贡献规则)

## Existing Awesome Lists / 已有 Awesome 列表

- [sindresorhus/awesome](https://github.com/sindresorhus/awesome) - The canonical
  Awesome list index and style reference. Useful for list hygiene, not loop
  design.
  - 中文：Awesome List 的事实标准入口，可参考其精选原则和结构风格。
- [ChaoYue0307/awesome-loop-engineering](https://github.com/ChaoYue0307/awesome-loop-engineering)
  - Curated resources and practical patterns for loop engineering with AI and
    coding agents.
  - 中文：已经成型的 Loop Engineering 资料与模式集合，可作为学习入口和资料索引。
- [invincible04/awesome-loop-engineering](https://github.com/invincible04/awesome-loop-engineering)
  - Teaching-oriented loop engineering repo with an annotated reading list,
    prompts, examples, and a portable agent skill.
  - 中文：更像课程式仓库，适合参考如何把 Loop Engineering 做成可学习、可运行的公开项目。
- [rudy2steiner/awesome-agent-loops](https://github.com/rudy2steiner/awesome-agent-loops)
  - A compact Awesome-style list for loop engineering patterns, tools, and
    templates for AI coding agents.
  - 中文：较小但主题集中，适合作为 agent loop 资源补充。
- [YennNing/Awesome-Code-as-Agent-Harness-Papers](https://github.com/YennNing/Awesome-Code-as-Agent-Harness-Papers)
  - Research-oriented list for code-as-agent-harness papers and mechanisms.
  - 中文：偏论文和 harness 机制，适合补充 loop 运行时、状态、工具和失败恢复视角。
- [awesome-agentic-patterns](https://github.com/nibzard/awesome-agentic-patterns)
  - Curated agentic AI patterns and production tricks.
  - 中文：面向 agentic pattern 的资料集合，适合作为模式索引，但具体 loop
    合同仍需再工程化。
- [Awesome Copilot - Agentic Workflows](https://awesome-copilot.github.com/learning-hub/agentic-workflows/)
  - GitHub-oriented agentic workflows, trigger models, and repository automation
    examples.
  - 中文：偏 GitHub Actions / 仓库自动化场景，适合参考 schedule、event、slash
    command 等触发方式。

## Core Papers, Guides, and Articles / 核心指南与文章

- [Anthropic - Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
  - Distinguishes workflows from agents and describes prompt chaining, routing,
    parallelization, orchestrator-worker, and evaluator-optimizer patterns.
  - 中文：对 workflow 与 agent 的边界、编排模式和 evaluator-optimizer loop
    很有参考价值。
- [OpenAI - A Practical Guide to Building Agents](https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/)
  - Covers agent design, orchestration, model choice, tools, guardrails, and
    multi-agent patterns.
  - 中文：适合作为 agent 产品化设计的总体框架，尤其是 tool、handoff、guardrail
    和成本/延迟权衡。
- [OpenAI Agents SDK - Agents guide](https://developers.openai.com/api/docs/guides/agents)
  - Practical docs for agent definitions, runs, orchestration, handoffs,
    guardrails, human review, state, integrations, and observability.
  - 中文：对 Looper Creator 的 runtime adapter、handoff、human review 和
    observability 字段有直接启发。
- [OpenAI Agents SDK - Guardrails](https://openai.github.io/openai-agents-python/guardrails/)
  - Shows how guardrails attach to inputs, outputs, and tool use, and where they
    do not apply.
  - 中文：提醒 schema 不能只写“有 guardrail”，还要明确适用边界和绕过风险。
- [OpenAI Agents SDK - Tracing](https://openai.github.io/openai-agents-python/tracing/)
  - Explains traces for model calls, tool calls, handoffs, guardrails, and custom
    events.
  - 中文：支撑 Looper Creator 中 `journal.jsonl`、evidence refs、monitoring
    plan 等可追踪性设计。
- [OpenAI - AGENTS.md for Codex](https://developers.openai.com/codex/guides/agents-md)
  - Project instructions loaded by Codex before work starts.
  - 中文：支撑 Codex runtime adapter 输出 `AGENTS.md`，让 loop 合同进入执行上下文。
- [Andrew Ng - Agentic workflow patterns](https://x.com/AndrewYNg/status/1773393357022298617)
  - The four common patterns: reflection, tool use, planning, and multi-agent
    collaboration.
  - 中文：支撑 Looper Creator 的 decomposition、reflection/review、tool/verifier
    和 multi-agent collaboration 字段。
- [GitHub Community - Agentic Workflows technical preview](https://github.com/orgs/community/discussions/186451)
  - Emphasizes defined terms, reports/issues/PRs, and human review before merge.
  - 中文：支撑 Looper Creator 的 human gate、不可逆动作门禁和仓库自动化边界。

## Courses and Learning Paths / 课程与学习路径

- [DeepLearning.AI - Agentic AI](https://www.deeplearning.ai/courses/agentic-ai)
  - Andrew Ng's course on iterative, multi-step workflows and the core agentic
    design patterns.
  - 中文：适合作为 agentic workflow 入门主线，覆盖反思、工具、规划和多 agent。
- [DeepLearning.AI - AI Agents in LangGraph](https://www.deeplearning.ai/courses/ai-agents-in-langgraph)
  - Builds an agent from scratch and then rebuilds it with LangGraph.
  - 中文：适合理解 agent loop 从手写循环到图式状态机的迁移。
- [LangChain Academy - Introduction to LangGraph](https://academy.langchain.com/courses/intro-to-langgraph)
  - Includes human-in-the-loop, breakpoints, editing state, time travel,
    parallelization, and sub-graphs.
  - 中文：适合学习 durable state、人工中断、回放和子图拆解。
- [DeepLearning.AI - Multi AI Agent Systems with crewAI](https://www.deeplearning.ai/courses/multi-ai-agent-systems-with-crewai)
  - Role-based multi-agent task decomposition.
  - 中文：适合参考角色化 agent、目标与任务分配。
- [DeepLearning.AI - AI Agentic Design Patterns with AutoGen](https://www.deeplearning.ai/courses/ai-agentic-design-patterns-with-autogen)
  - Implements reflection, tool use, planning, and multi-agent collaboration with
    AutoGen.
  - 中文：适合把 agentic design patterns 落成可运行 multi-agent 会话。
- [Hugging Face Agents Course](https://huggingface.co/learn/agents-course/en/unit1/introduction)
  - Open learning path for tools, agents, multi-agent systems, and evaluation.
  - 中文：适合开源生态学习与实践，配套 GitHub 仓库见下方。

## GitHub Projects and Frameworks / GitHub 项目与框架

- [langchain-ai/langgraph](https://github.com/langchain-ai/langgraph)
  - Stateful agent orchestration with durable execution, human-in-the-loop, and
    recoverable long-running agents.
  - 中文：对 Looper Creator 的 `state.json`、`PROGRESS.md`、受阻恢复和
    supervisor design 最有参考价值。
- [microsoft/autogen](https://github.com/microsoft/autogen)
  - Multi-agent applications that can work autonomously or alongside humans.
  - 中文：适合参考多 agent 对话、工具、人类反馈和团队协作模式。
- [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI)
  - Role-based crews and event-driven flows for multi-agent automation.
  - 中文：适合参考角色、目标、任务、团队协同与业务流程自动化。
- [microsoft/semantic-kernel](https://github.com/microsoft/semantic-kernel)
  - Model-agnostic SDK for agents, multi-agent systems, and enterprise
    orchestration.
  - 中文：适合参考企业级 agent 编排、过程框架和多语言实现。
- [huggingface/agents-course](https://github.com/huggingface/agents-course)
  - Open-source course repository for the Hugging Face agents curriculum.
  - 中文：适合作为学习型项目的参考，包含课程单元、实践材料和开源协作方式。
- [crewAIInc/crewAI-examples](https://github.com/crewAIInc/crewAI-examples)
  - End-to-end examples for CrewAI applications.
  - 中文：适合查找实际 multi-agent 应用样例，而不是只看框架 API。
- [Azure-Samples/semantic-kernel-workshop](https://github.com/Azure-Samples/semantic-kernel-workshop)
  - Workshop notebooks for Semantic Kernel, agents, and process workflows.
  - 中文：适合课程式学习 enterprise workflow 与 agent orchestration。

## Runtime and Instruction Standards / 运行时与指令标准

- [Codex AGENTS.md](https://developers.openai.com/codex/guides/agents-md)
  - Use project-level instructions so the loop contract is loaded before work.
  - 中文：让 loop 的执行规则变成 runtime 可发现上下文。
- [LangChain Human-in-the-Loop middleware](https://docs.langchain.com/oss/python/langchain/human-in-the-loop)
  - Policy-driven interrupt/approval before sensitive tool calls.
  - 中文：支撑 Looper Creator 中“代理决策必须先经用户授权，不可越过高风险门禁”的设计。
- [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview)
  - Highlights durable execution, streaming, and human-in-the-loop as core
    orchestration capabilities.
  - 中文：说明长 loop 需要状态持久化和可恢复执行，而不是依赖对话历史。
- [OpenAI new tools for building agents](https://openai.com/index/new-tools-for-building-agents/)
  - Introduces agent primitives: agents, handoffs, guardrails, and tracing.
  - 中文：适合作为 runtime adapter 设计的基础术语来源。

## How Looper Creator Uses These Ideas / Looper Creator 如何吸收这些思想

| Idea / 思想 | Source / 来源 | Looper Creator implementation / 落地方式 |
| --- | --- | --- |
| Workflows vs. agents / workflow 与 agent 边界 | Anthropic Building Effective Agents | `loop_nodes` distinguish workflow, agent loop, reflection loop, evaluator-optimizer loop, parallel section, handoff loop, and human gate. |
| Agentic design patterns / agentic 设计模式 | Andrew Ng / DeepLearning.AI | `decomposition_policy`, `collaboration_policy`, reviewer/reflection tasks, and multi-agent activation. |
| Durable state / 持久状态 | LangGraph | `state.json`, `journal.jsonl`, `PROGRESS.md`, generated evidence paths, and context reload rules. |
| Human-in-the-loop / 人工确认 | LangGraph HITL, OpenAI Agents SDK, GitHub Agentic Workflows | `human_gates`, `decision_policy.user_confirmation`, `proxy_decision_agent.default_when_uncertain`, irreversible action gates. |
| Guardrails / 门禁 | OpenAI Agents SDK Guardrails | `verification_policy`, protected paths, anti-gaming rules, verifier scripts, and high-risk decision rejection. |
| Tracing / 可追踪性 | OpenAI Agents SDK Tracing | `journal.jsonl`, evidence refs, `monitoring-plan.json`, `DECISIONS.md`. |
| Runtime instructions / 运行时指令 | Codex AGENTS.md, Claude Code, Cursor rules | `execution_adapters`, `runtime.json`, selected adapter generation. |
| Awesome list hygiene / Awesome 列表质量 | sindresorhus/awesome | Curated list with clear criteria instead of an unbounded link dump. |

## Contribution Rules / 贡献规则

- Add a resource only when it teaches a reusable loop design, execution,
  verification, or supervision pattern.
- Prefer official docs, primary GitHub repos, maintained examples, or courses
  with runnable material.
- Include one English sentence and one Chinese sentence explaining why the
  resource matters.
- Avoid listing paid marketing pages unless they contain concrete technical
  material.
- Keep links stable and avoid duplicating the same project under many sections.
