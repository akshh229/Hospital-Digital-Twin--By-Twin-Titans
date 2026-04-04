# Active Intervention Visibility

## Goal

Expose currently engaged interventions directly in the command center so operators can see which levers are affecting live capacity and resource behavior without inferring it from recommendations alone.

## Scope

- Extend the operations overview contract with `simulation.active_interventions`
- Derive active interventions from simulation state modifiers
- Render visible intervention chips in the command center hero
- Render a dedicated active intervention summary inside the simulation control panel
- Verify backend tests, frontend build, and live API behavior

## Implementation

### Backend

- Added `ActiveInterventionResponse` to the simulation response contract
- Added `_build_active_interventions(state)` to map live state modifiers into operator-facing labels, values, and effects
- Included `active_interventions` in the simulation payload returned by the operations overview

### Frontend

- Added `ActiveIntervention` typing to the shared frontend contract
- Rendered active intervention cards in the command center hero surface
- Added an active intervention summary block to the simulation control panel

## Verification

- `docker exec lazarus-backend pytest -q tests/test_operations_center.py tests/test_api_endpoints.py`
- `npm run build`
- Live verification:
  - `POST /api/ops/control` with `{"action":"apply_intervention","intervention_id":"open-surge-beds"}`
  - `GET /api/ops/overview` confirms `simulation.active_interventions[0].id = "open-surge-beds"`
  - `POST /api/ops/control` with `{"action":"reset"}` clears active interventions
