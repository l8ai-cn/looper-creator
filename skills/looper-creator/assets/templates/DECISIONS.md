# Blocked Execution Decisions

## User Confirmation

- Delegation confirmed: pending
- Confirmation record: `PROGRESS.md`

## Proxy Decision Agent

- Agent: `decision-proxy`
- Authority: `delegated_low_risk`
- Default when uncertain: `ask_user`

Allowed decisions:

- choose next atomic task
- split task smaller
- retry verifier once

Forbidden decisions:

- irreversible action
- production deploy
- credential change

## Decision Log

Record blocked reason, options, selected option, rationale, evidence ref, and
whether supervisor review is required.
