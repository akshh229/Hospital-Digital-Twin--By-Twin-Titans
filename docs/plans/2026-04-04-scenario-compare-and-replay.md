# Scenario Compare And Replay Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a command-center comparison view for `baseline vs current scenario` plus a replay scrubber that lets reviewers step through recent operational events.

**Architecture:** Extend the backend operations payload with two presentation-ready structures: a scenario comparison block built from the same patient cohort under baseline and current assumptions, and a reconstructed replay frame list derived from recent command-room events. Then render those structures in dedicated command-center panels with minimal frontend-only logic.

**Tech Stack:** FastAPI, Pydantic, React, TypeScript, pytest, Vite

---

### Task 1: Add the comparison and replay contract

**Files:**
- Modify: `backend/app/schemas/operations.py`
- Modify: `backend/app/services/operations_center.py`
- Test: `backend/tests/test_operations_center.py`
- Test: `backend/tests/test_api_endpoints.py`

**Steps:**
- Add failing tests for scenario comparison deltas and replay frame generation
- Add response models for comparison metrics and replay frames
- Build helper functions for:
  - baseline/current summary comparison
  - baseline/current resource comparison
  - reconstructed replay checkpoints
- Re-run focused backend tests

### Task 2: Render comparison and replay in the dashboard

**Files:**
- Create: `frontend/src/components/ScenarioComparisonPanel.tsx`
- Modify: `frontend/src/components/PatientFlowTimeline.tsx`
- Modify: `frontend/src/pages/CommandCenter.tsx`
- Modify: `frontend/src/types/index.ts`

**Steps:**
- Add frontend types for comparison metrics and replay frames
- Render a scenario comparison panel below the briefing row
- Upgrade the timeline panel with a replay scrubber and active checkpoint detail
- Re-run frontend build

### Task 3: Verify the slice

**Steps:**
- `docker exec lazarus-backend pytest -q tests/test_operations_center.py tests/test_api_endpoints.py`
- `npm run build` in `frontend`
- Live `GET http://localhost/api/ops/overview` should now include:
  - `scenario_comparison`
  - `replay_frames`
