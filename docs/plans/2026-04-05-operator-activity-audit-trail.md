# Operator Activity Audit Trail

## Goal

Expose a first-class operator activity log so the ICU command center shows who changed the simulator posture, what action was taken, and the latest operational state without relying on generic timeline cards alone.

## Problems To Solve

- The command center records simulator events, but operators do not get a dedicated audit surface for recent control changes.
- `last_action` exists in state, but it does not explain the action in human language or capture a timestamp for non-intervention controls.
- The UI does not distinguish generic patient-flow events from direct operator actions like speed changes, crisis injection, pause/resume, or intervention lifecycle updates.

## Scope

- Extend simulation state with human-readable latest-action metadata
- Add structured operator activity entries to the operations overview contract
- Emit richer action metadata for simulator controls, crisis injection, intervention apply, and intervention rollback events
- Add a command-center panel focused on latest operator posture and recent activity history
- Verify backend tests, frontend tests, and frontend build

## Implementation Plan

### Backend

- Add `last_action_at` to shared simulator state
- Add `last_action_label` to the simulation response payload
- Add an `operator_activity` collection to the operations overview payload
- Enrich operator-generated simulation events with:
  - `action_key`
  - `action_label`
  - optional `intervention_id`
  - optional `scenario_label`
  - optional `speed`
- Build operator activity entries from the structured simulator event stream

### Frontend

- Extend shared types for simulation action metadata and operator activity entries
- Create an `OperatorActivityPanel` that shows:
  - the latest operator posture
  - active intervention count
  - current scenario and playback state
  - a recent operator action log
- Integrate the panel into the command center beside the simulator controls

## Verification

- Focused pytest coverage for:
  - operator activity serialization
  - structured action metadata emission
  - latest action labeling
- Frontend test run
- Frontend production build
