# Incident Handoff Export

## Goal

Turn the live ICU command-center state into a shareable incident handoff artifact so operators can export the current situation, actions taken, and recommended next steps without leaving the app.

## Problems To Solve

- The command center is highly informative on screen but does not produce a concise handoff package for shift changes, demos, or incident review.
- Operators have no one-click way to export the current situation as a structured JSON artifact or a human-readable markdown summary.
- The existing panels distribute context across multiple surfaces instead of packaging it into a single shareable report.

## Scope

- Add a structured incident handoff object to the operations overview contract
- Generate export-ready markdown from the current ICU state
- Surface current command metrics, immediate risks, active interventions, recent actions, and next steps
- Add a command-center panel with copy and download actions
- Verify backend tests, frontend tests, and frontend build

## Implementation Plan

### Backend

- Add an `incident_handoff` payload to the operations overview response
- Build a structured handoff summary from:
  - current scenario and command status
  - ICU pressure metrics
  - immediate risks
  - active interventions
  - recent operator actions
  - recommended next steps
- Include markdown output and a suggested export filename

### Frontend

- Extend shared types for the incident handoff payload
- Add an `IncidentHandoffPanel` with:
  - command summary
  - risks and next-step sections
  - copy markdown action
  - JSON download action
- Integrate the panel into the command-center workflow near the operator controls

## Verification

- Focused pytest coverage for incident handoff generation
- API payload coverage for overview serialization
- Frontend render test for the handoff panel
- Frontend test run
- Frontend production build
