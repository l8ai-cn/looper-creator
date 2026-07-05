# Loop Name

## Purpose

State the user goal, business value, done definition, and explicit non-goals.

## Clarification Policy

- Ambiguity triggers:
- Secondary user query:
- Low-risk assumptions allowed:
- Block if:

## Recursive Loop Topology

List loop nodes as a recursive task graph. Each node needs:

- id
- type
- purpose
- entry conditions
- exit conditions
- steps
- context pack
- agent assignments
- verification refs
- children when the task must be decomposed further

## Atomic Tasks

Each task must be independently verifiable and fit inside its context budget.

## Acceptance Checklist

Define the `ACCEPTANCE.md` path, update policy, and one checklist item per
atomic task. A checkbox may be checked only after criteria, verifier refs, and
evidence refs are satisfied.

## Agents

Define orchestrator, worker, reviewer, verifier, and domain specialist roles only
when they are needed by the loop.

## Context Strategy

Define required context, retrieval strategy, trimming policy, compaction threshold,
durable memory paths, and excluded context.

## Termination Policy

Define success, failure, budget exits, no-progress exits, and human gates.

## Verification

List deterministic verifiers and protected paths. Do not accept agent self-report
as terminal evidence.
