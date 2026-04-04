# Submission Assets

## Generated Screenshot Set

The current submission-ready screenshots are stored in the repository root:

- `screenshots/01-command-center-overview.png`
- `screenshots/02-command-center-crisis-response.png`
- `screenshots/03-patient-drilldown.png`

All screenshots are exported at `1440x900` viewport with `2x` device scale for
retina-quality output.

## What Each Screenshot Shows

### 1. Command Center Overview

File:
`screenshots/01-command-center-overview.png`

Use for:
- cover image
- first gallery image
- architecture/UX overview

Suggested caption:
`Live ICU command center with bed allocation, resource forecasting, and patient flow awareness.`

### 2. Crisis Response View

File:
`screenshots/02-command-center-crisis-response.png`

Use for:
- operations under stress
- simulation/control story
- “why this matters” slide

Suggested caption:
`The digital twin reacts to an injected respiratory crisis by forecasting oxygen pressure, staffing load, and overflow risk in real time.`

### 3. Patient Drill-Down

File:
`screenshots/03-patient-drilldown.png`

Use for:
- clinical detail view
- explainability
- command-to-bedside continuity

Suggested caption:
`Patient-level drill-down connects telemetry, escalation history, medication schedule, and live routing context back to the ICU command center.`

## How To Regenerate

From the frontend workspace:

```bash
npm run build
npm run capture:screenshots
```

## Implementation Notes

- The screenshot script lives at:
  `frontend/scripts/capture-submission-screenshots.mjs`
- The script serves the production build locally and mocks the API/WebSocket
  layer in Playwright so screenshots can be regenerated without requiring the
  Docker stack to be running.

## Recommended Submission Order

1. `01-command-center-overview.png`
2. `02-command-center-crisis-response.png`
3. `03-patient-drilldown.png`

This order tells the clearest story:
overview -> crisis simulation -> patient-level response.
