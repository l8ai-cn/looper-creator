# Acceptance Checklist

## Operating Rules

- Keep one checklist item per atomic task.
- Check an item only after its criteria pass, verifier refs pass, and evidence refs exist.
- Reopen an item if later verification invalidates its evidence.
- Terminal success requires all items checked and the terminal verifier passing.

## Items

- [ ] `accept-task-1`: Complete one independently verifiable task slice.
  - Atomic task: `task-1`
  - Owner agent: `worker`
  - Acceptance criteria:
    - linked verifier exits 0
  - Verification refs:
    - `terminal`
  - Evidence refs:
    - artifact ref
    - evidence ref
