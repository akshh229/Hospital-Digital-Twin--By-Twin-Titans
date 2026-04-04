# Operator-Aware Recommendations

## Goal

Upgrade the hospital digital twin recommendation layer so the command center can distinguish between executable interventions, simulator control actions, and advisory guidance while showing whether a recommendation is already active and what impact has actually been observed.

## Problems To Solve

- The recommendation panel currently treats every recommendation like an intervention even when some are advisory or simulator-control guidance.
- Applied interventions are not reflected back into the recommendation cards as active or saturated states.
- The panel shows projected effect but does not show what actually changed after an operator applies an intervention.

## Scope

- Extend the recommendation response contract with execution metadata
- Add recommendation state metadata and observed impact fields
- Capture intervention baseline metrics before simulation changes are applied
- Compare current state to the captured baseline for recent interventions
- Update the frontend recommendation panel to render execution-aware controls and stateful impact summaries
- Verify backend tests, frontend build, and live recommendation execution

## Implementation Plan

### Backend

- Add execution metadata for each recommendation:
  - `action_type`
  - optional `control_action`
  - `can_apply`
  - `apply_label`
- Add state metadata:
  - `state`
  - `state_label`
  - `state_reason`
- Add observed impact fields:
  - `observed_summary`
  - `observed_metrics`
- Persist the most recent intervention baseline in simulation state before applying an intervention
- Build recommendation state from active modifiers and most recent intervention history

### Frontend

- Update shared recommendation types
- Route recommendation actions by execution type
- Render advisory recommendations without fake apply buttons
- Show active, saturated, and recently applied state labels
- Show observed impact beside projected impact when data is available

## Verification

- Focused pytest coverage for:
  - recommendation execution metadata
  - active or saturated recommendation states
  - observed metrics after an applied intervention
- Frontend production build
- Live verification of:
  - intervention recommendations applying through `/api/ops/control`
  - control recommendations triggering the correct simulator action
  - advisory recommendations rendering without execution affordances
