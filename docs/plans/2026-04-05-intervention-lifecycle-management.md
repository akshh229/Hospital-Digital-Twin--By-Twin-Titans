# Intervention Lifecycle Management

## Goal

Allow hospital digital twin operators to step down or fully clear active interventions without resetting the entire simulator state.

## Problems To Solve

- Active interventions are visible but cannot be reduced or removed individually.
- Operators must currently use a full simulator reset to unwind support actions, which also discards the surrounding scenario state.
- The command center does not expose a safe lifecycle path for de-escalating surge beds, oxygen reserve protection, or staffing support.

## Scope

- Extend the active intervention response contract with lifecycle control metadata
- Add simulator control actions for stepping down or clearing a targeted intervention
- Implement backend rollback logic for surge beds, oxygen reserve buffering, and staffing support
- Keep intervention observation history coherent after lifecycle changes
- Add operator lifecycle controls to the simulation control panel
- Verify backend tests, frontend tests, and frontend build

## Implementation Plan

### Backend

- Extend `active_interventions` payload items with:
  - `can_step_down`
  - `step_down_label`
  - `can_clear`
  - `clear_label`
- Add `step_down_intervention` and `clear_intervention` to the simulator control request contract
- Implement targeted lifecycle handling that:
  - removes one configured intervention increment when stepping down
  - returns the intervention to baseline when clearing
  - captures a pre-change baseline for observed impact comparisons
  - emits a timeline event describing the rollback action

### Frontend

- Update shared simulation types for lifecycle actions and active intervention controls
- Add lifecycle buttons to the active interventions panel
- Adjust recommendation observation copy so it remains accurate after non-apply operator actions

## Verification

- Focused pytest coverage for:
  - active intervention lifecycle metadata
  - step-down simulator control handling
  - clear simulator control handling
  - lifecycle control API requests
- Frontend test run
- Frontend production build
