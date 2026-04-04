# Closed-Loop Intervention Projections Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade command-center recommended actions so each action includes a modeled 30-minute projected impact on ICU pressure and resource posture.

**Architecture:** Keep the existing `/api/ops/overview` flow, but enrich `recommended_actions` with intervention-specific projection data built from the current summary and resource cards. Then surface those projections directly inside the action cards so operators can compare likely effect without leaving the dashboard.

**Tech Stack:** FastAPI, Pydantic, React, TypeScript, pytest, Vite

---

### Task 1: Model intervention projections in the backend

**Files:**
- Modify: `backend/app/schemas/operations.py`
- Modify: `backend/app/services/operations_center.py`
- Test: `backend/tests/test_operations_center.py`
- Test: `backend/tests/test_api_endpoints.py`

**Steps:**
- Add failing tests for projected intervention outcomes
- Add projection models to recommended actions
- Implement lightweight outcome modeling for high-value actions
- Re-run focused backend tests

### Task 2: Render projected impact in the dashboard

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/components/RecommendedActionsPanel.tsx`

**Steps:**
- Extend frontend types for projected metrics
- Show a concise projected outcome strip on each action card
- Re-run frontend build

### Task 3: Verify the slice

**Steps:**
- `docker exec lazarus-backend pytest -q tests/test_operations_center.py tests/test_api_endpoints.py`
- `npm run build` in `frontend`
- Live `GET http://localhost/api/ops/overview` should show projected metrics inside `recommended_actions`
