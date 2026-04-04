# Executable Intervention Controls Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn projected command-center actions into executable controls that update the live ICU digital twin state through the existing `/api/ops/control` flow.

**Architecture:** Extend the simulation state with a small set of intervention modifiers, add an `apply_intervention` control action, and let the overview rebuild from that adjusted state. Then wire the action cards to call the same control mutation path already used by the simulation panel.

**Tech Stack:** FastAPI, Redis-backed state store, SQLAlchemy, React, TypeScript, pytest, Vite

---

### Task 1: Add red tests for executable interventions

**Files:**
- Modify: `backend/tests/test_operations_center.py`
- Modify: `backend/tests/test_api_endpoints.py`

**Steps:**
- Add failing tests for:
  - dynamic surge-bed capacity in the overview
  - boosted oxygen/staff resources from applied interventions
  - `apply_intervention` control flow
  - control payload accepting `intervention_id`

### Task 2: Implement backend intervention state and control flow

**Files:**
- Modify: `backend/app/services/ops_store.py`
- Modify: `backend/app/schemas/operations.py`
- Modify: `backend/app/services/operations_center.py`

**Steps:**
- Extend stored simulation state with intervention modifiers
- Update overview calculations to honor those modifiers
- Add `apply_intervention` action handling
- Append intervention events for timeline/replay visibility

### Task 3: Wire intervention execution into the dashboard

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/components/RecommendedActionsPanel.tsx`
- Modify: `frontend/src/pages/CommandCenter.tsx`

**Steps:**
- Extend the control request type with `intervention_id`
- Add “Apply now” action buttons to recommended actions
- Route button clicks through the existing simulation mutation

### Task 4: Verify the slice

**Steps:**
- `docker exec lazarus-backend pytest -q tests/test_operations_center.py tests/test_api_endpoints.py`
- `npm run build` in `frontend`
- Live `POST http://localhost/api/ops/control` with `apply_intervention` should return an updated overview
