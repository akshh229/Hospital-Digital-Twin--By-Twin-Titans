# Command Center Clarity Pack Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a first-pass command-center clarity layer with trust signals, last-15-minute briefing, recommended operational actions, and stronger patient explainability in both the command center and drill-down view.

**Architecture:** Extend the backend `/api/ops/overview` contract so the command center gets one opinionated, presentation-ready payload instead of frontend-only heuristics. Then render that richer contract in new dashboard panels and reuse the same explainability data in the patient drill-down so the operator and clinician views stay aligned.

**Tech Stack:** FastAPI, Pydantic, SQLAlchemy, React, TypeScript, Vite, pytest

---

### Task 1: Save the New Overview Contract

**Files:**
- Modify: `backend/app/schemas/operations.py`
- Modify: `backend/app/services/operations_center.py`
- Test: `backend/tests/test_operations_center.py`
- Test: `backend/tests/test_api_endpoints.py`

**Step 1: Write failing backend tests**

- Add coverage for:
  - patient risk reasons derived from vitals and alert state
  - trust signal shape and freshness labels
  - recommended action generation under overflow or resource stress
  - `/api/ops/overview` serializing the new fields

**Step 2: Run focused backend tests to verify failure**

Run:

```powershell
pytest -q backend/tests/test_operations_center.py backend/tests/test_api_endpoints.py
```

Expected:
- failures for missing fields such as `risk_reasons`, `trust`, `briefing`, or `recommended_actions`

**Step 3: Implement the minimal backend contract**

- Add new response models for:
  - `OperationsBriefingResponse`
  - `OperationsTrustResponse`
  - `RecommendedActionResponse`
- Add `risk_reasons` to bed and queue patient payloads
- Build helper functions in `operations_center.py` for:
  - risk-reason generation
  - telemetry/trust summarization
  - briefing generation
  - recommended action generation

**Step 4: Re-run focused backend tests**

Run:

```powershell
pytest -q backend/tests/test_operations_center.py backend/tests/test_api_endpoints.py
```

Expected:
- all targeted backend tests pass

### Task 2: Render the New Command-Center Panels

**Files:**
- Create: `frontend/src/components/OperationsBriefingPanel.tsx`
- Create: `frontend/src/components/RecommendedActionsPanel.tsx`
- Modify: `frontend/src/pages/CommandCenter.tsx`
- Modify: `frontend/src/types/index.ts`

**Step 1: Extend the frontend types**

- Add interfaces for:
  - briefing
  - trust
  - recommended actions
  - risk reasons on bed and queue entries

**Step 2: Build the new panels**

- `OperationsBriefingPanel.tsx`
  - show a “last 15 minutes” style narrative
  - show trust/freshness badges
  - show top operational changes
- `RecommendedActionsPanel.tsx`
  - show top 3 actions with priority and owner hints

**Step 3: Insert the panels into the command center**

- Place them directly below the hero so the operator sees them before bed-map scanning

**Step 4: Run frontend build**

Run:

```powershell
cd frontend
npm run build
```

Expected:
- successful TypeScript and Vite build

### Task 3: Strengthen Patient Explainability

**Files:**
- Modify: `frontend/src/components/ICUBedHeatmap.tsx`
- Modify: `frontend/src/components/PatientCommandSnapshot.tsx`
- Modify: `frontend/src/pages/PatientDetail.tsx`

**Step 1: Add “why this patient is high risk” to bed and queue cards**

- Render 1-2 risk reasons on occupied beds and triage entries

**Step 2: Add a patient summary strip in the drill-down**

- Reuse routing context to show:
  - primary concern
  - support posture
  - next likely action

**Step 3: Re-run frontend build**

Run:

```powershell
cd frontend
npm run build
```

Expected:
- build stays green after the drill-down changes

### Task 4: Verify the Vertical Slice End-to-End

**Files:**
- Verify: `backend/tests/test_operations_center.py`
- Verify: `backend/tests/test_api_endpoints.py`
- Verify: `frontend`
- Verify: live Docker stack

**Step 1: Run focused backend tests**

```powershell
docker exec lazarus-backend pytest -q tests/test_operations_center.py tests/test_api_endpoints.py
```

**Step 2: Build the frontend**

```powershell
cd frontend
npm run build
```

**Step 3: Verify the live overview payload**

```powershell
Invoke-WebRequest -Uri 'http://localhost/api/ops/overview' | Select-Object -ExpandProperty Content
```

Expected:
- payload includes `briefing`, `trust`, `recommended_actions`, and patient `risk_reasons`

**Step 4: Spot-check live UX semantics**

- Confirm the command center now answers:
  - what changed recently
  - how trustworthy/fresh the simulation is
  - what the ops lead should do next
  - why a given patient is being escalated
