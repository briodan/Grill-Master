# Documentation System

This folder is organized by **feature**. Each feature must keep three documentation artifacts current:

1. **Primary feature doc** in the feature folder root: `<feature-name>.md`
2. **Behavior baseline** in the feature folder root: `baseline.md`
3. **Decision/context trail** in `trail/` as dated entries
4. **Related SQL** in `sql/` if applicable

## Required Feature Structure

```text
documentation/
  features/
    <feature-name>/
      <feature-name>.md
      baseline.md
      trail/
        YYYY-MM-DD-<short-title>.md
      sql/
        schema-definitions.sql
        example-queries.sql
```

## File Roles

### `<feature-name>.md` (primary)

- Explains what the feature does today.
- Includes user flow, technical flow, and integration points.
- Should be readable by developers and support engineers.

### `baseline.md`

- Captures expected behavior and invariants.
- Serves as the "known-good" reference for regression checks.
- Update only when intended behavior changes.

### `trail/*.md`

- One file per significant decision or behavior clarification.
- Contains context, alternatives considered, and rationale.
- Use date-prefixed filenames for chronological history.

## Update Rules

When code changes affect a feature:

1. Update `<feature-name>.md` for current behavior and flow.
2. Update `baseline.md` if expected behavior changed.
3. Add a new `trail/` entry for non-trivial decisions, constraints, or tradeoffs.
4. Never modify a `trail/` entry outside of the date it was created. If a change invalidates a past decision, add a new entry explaining the change and its impact on the original decision.

If a change does **not** alter behavior, baseline can remain unchanged.

## Feature Map

Current feature folders:

- `features/ha-integration` - Home Assistant custom integration: sensors, climate control, cloud sync
- `features/grill-communication` - HTTP RPC protocol details, MCU payload format, command encoding
- `planning/` - Project plan and phase planning

## Documentation Quality Bar

When updating feature docs, prefer concrete facts from code over generic statements:

- Name key classes/methods involved.
- Document important constants and timing (for example, polling intervals).
- Capture failure behavior and graceful-degradation paths.
- Keep feature boundaries clear to avoid duplicate or conflicting docs.
- Reflect actual behavior as implemented today, not desired future behavior.

## Recommended Update Checklist (per feature)

1. Confirm affected code paths/classes.
2. Update `<feature>.md` (current flow and integration points).
3. Update `baseline.md` if expected behavior changed.
4. Add a `trail` entry when decisions/tradeoffs changed.
5. Verify related feature docs remain consistent.

## Trail Entry Template

```md
# <Decision Title>

- Date: YYYY-MM-DD
- Feature: <feature-name>
- Related code: <paths>

## Context

...

## Decision

...

## Alternatives Considered

- Option A: ...
- Option B: ...

## Consequences

- Positive: ...
- Negative: ...
```
