# Looper Creator

[English](README.md) | [简体中文](README.zh-CN.md)

Looper Creator 是一个用于创建 **递归式 Loop 编排项目** 的 Codex Skill。它把目标拆成
可验证、可追踪、可停止的工作循环，并内置上下文策略、多 Agent 协作、门禁、受阻处理、
验收清单和运行时适配。

本项目刻意保持严格：语义不明、缺少澄清策略、缺少验证器、缺少停止条件、无边界子
Agent、静默 fallback 等问题会被拒绝，而不是被包装成“继续执行”。

[![Awesome](https://awesome.re/badge.svg)](AWESOME-LOOP-ENGINEERING.md)
[![CI](https://github.com/l8ai-cn/looper-creator/actions/workflows/ci.yml/badge.svg)](https://github.com/l8ai-cn/looper-creator/actions/workflows/ci.yml)

## 快速入口

- [中英双语学习资源](AWESOME-LOOP-ENGINEERING.md)
- [Manifest Schema](skills/looper-creator/schemas/loop-manifest.schema.json)
- [Loop 示例](skills/looper-creator/examples)
- [生成项目模板](skills/looper-creator/assets/templates)

## 学习资源

请先看 [Awesome Loop Engineering](AWESOME-LOOP-ENGINEERING.md)。这是一个中英文
学习地图和参考来源账本，包含：

- 已有 Awesome Loop Engineering / Agent Loop 列表
- Anthropic、Claude、OpenAI、LangGraph 等官方或一手资料
- Andrew Ng、DeepLearning.AI、LangChain Academy、Hugging Face 的课程
- LangGraph、AutoGen、CrewAI、Semantic Kernel 等 GitHub 项目
- Looper Creator 如何把这些知识落实到 schema、模板、门禁和运行时适配中

## 支持这个项目

如果 Looper Creator 帮你设计了更可靠的 Agent Loop，请在 GitHub 上支持这个项目：

- Star：收藏项目，也帮助更多人发现它。
- Watch：关注 schema、模板和运行时适配更新。
- Fork：把 Skill 改造成适合你自己团队或 Agent Runtime 的版本。

## 它会生成什么

生成的 Loop 项目包含：

```text
LOOP.md
PROGRESS.md
ACCEPTANCE.md
DECISIONS.md
loop.json
loops.json
tasks.json
agents.json
context-policy.json
state.json
journal.jsonl
runtime.json
monitoring-plan.json
scripts/verify.sh
ADAPTERS.md
AGENTS.md
```

其中 `loop.json` 是规范化 manifest，`state.json` 和 `journal.jsonl` 用于持久状态与
执行追踪，`ACCEPTANCE.md` 用于逐项验收，`DECISIONS.md` 用于记录受阻处理和代理决策。

v2 manifest 支持：

- 递归 / 多层次 loop 节点
- 原子任务拆解
- 必须由证据和验证器驱动的验收清单
- 用户语义不明时的二次询问策略
- 多 Agent 协作与子 Agent 激活策略
- Codex、Claude Code、Cursor 和 portable runtime 适配
- 上下文与 token 预算策略
- 受阻处理、用户确认的代理决策、supervisor 漂移监控
- 确定性验证、反作弊和不可弱化门禁
- 成功、失败、预算、无进展、人工门禁和升级退出条件
- 功能开发、测试排错、网站浏览器测试、部署、文档、标书和通用任务模板

## 仓库结构

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

## 安装

把 `skills/looper-creator` 复制到 Codex skills 目录：

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/looper-creator "${CODEX_HOME:-$HOME/.codex}/skills/"
```

然后在 Codex 中使用：

```text
Use $looper-creator to create a verified recursive loop project for my goal.
```

## 验证

验证 Skill 元数据：

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py skills/looper-creator
```

验证所有示例：

```bash
for f in skills/looper-creator/examples/*.loop.json; do
  case "$f" in
    *invalid*) python3 skills/looper-creator/scripts/validate_loop_project.py "$f" && exit 1 || true ;;
    *) python3 skills/looper-creator/scripts/validate_loop_project.py "$f" ;;
  esac
done
```

生成并验证一个示例 Loop 项目：

```bash
python3 skills/looper-creator/scripts/create_loop_project.py \
  --manifest skills/looper-creator/examples/feature-development.loop.json \
  --output /tmp/example-loop

python3 skills/looper-creator/scripts/validate_loop_project.py /tmp/example-loop
```

运行测试：

```bash
python3 -m unittest discover -s skills/looper-creator/tests
```

## 契约

公开契约是
`skills/looper-creator/schemas/loop-manifest.schema.json`。无依赖语义验证器是
`skills/looper-creator/scripts/validate_loop_project.py`。

schema 采用 English-first 结构字段，并通过 `metadata.locale` 支持本地化；也就是说，
机器可读字段稳定，用户可见内容可以按语言切换。

每个 manifest 必须定义 `acceptance_checklist`。生成项目会把它写入 `ACCEPTANCE.md`。
Agent 只能在验收标准、验证器引用和证据引用满足后逐项打勾；如果 `state.json` 已经进入
`complete`，但仍有未勾选项，`scripts/verify.sh` 会拒绝通过。

每个 manifest 也必须定义 `decision_policy`。生成项目会把受阻处理写入 `DECISIONS.md`，
把定期漂移检查写入 `monitoring-plan.json`。代理决策 Agent 只能处理用户确认过的低风险
受阻状态；高风险、不可逆、权限不清或对外动作仍然必须升级给用户。

语义验证器还会检查 JSON Schema 无法表达的契约：
`context_policy.durable_memory` 必须与 `state` 路径一致；每个原子任务必须有一个
checklist item；checklist 的验收标准、验证器引用和证据引用必须覆盖任务自身的验收标准、
验证器引用和输出产物。

## 公开仓库

项目已发布在
[github.com/l8ai-cn/looper-creator](https://github.com/l8ai-cn/looper-creator)。

克隆仓库：

```bash
git clone https://github.com/l8ai-cn/looper-creator.git
cd looper-creator
```

## 运行时适配

`loop.json` 是 canonical manifest。`runtime.json` 记录当前生成项目选择的 runtime
adapter。

默认只生成 Codex adapter：

```bash
python3 skills/looper-creator/scripts/create_loop_project.py \
  --manifest skills/looper-creator/examples/feature-development.loop.json \
  --output /tmp/example-loop \
  --runtime-target codex
```

也可以显式生成其他运行时：

```bash
python3 skills/looper-creator/scripts/create_loop_project.py \
  --manifest skills/looper-creator/examples/feature-development.loop.json \
  --output /tmp/claude-loop \
  --runtime-target claude_code
```

运行时文件映射：

- Codex: `AGENTS.md`
- Claude Code: `CLAUDE.md` 和可选 `.claude/settings.json`
- Cursor: `.cursor/rules/looper-creator.mdc`
- Portable: 只生成通用文件

未选中的 runtime adapter 文件不会生成到项目根目录。如果使用 `--force` 重新生成到不同
runtime，旧的未选中 adapter 文件会被移除。

运行时能力不足不能削弱验证。如果某个 runtime 不支持 manifest 声明的能力，必须
`block_and_report`，不能静默降级。

## License

MIT
