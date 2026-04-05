# Room Availability Feature Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a live room-availability feature to the command center so operators can see available ICU rooms/beds, filter the ward map, and understand where capacity exists right now.

**Architecture:** Keep this as a frontend-first feature built on the existing `bed_heatmap`, `summary`, and `triage_queue` payloads. Add a dedicated room-availability panel plus heatmap filtering so the feature improves operational decision-making without requiring a new backend contract.

**Tech Stack:** React 18, TypeScript, Tailwind CSS, Vitest, Testing Library

---

## Assumptions

- "Room availability" maps to the existing ICU bed/room allocation model already exposed through `bed_heatmap`.
- The current backend payload is sufficient for v1 because each bed already includes `bed_id`, `zone`, `status`, and assignment context.
- v1 should optimize operator clarity, not attempt predictive discharge modeling.

## Scope

- Add a dedicated `RoomAvailabilityPanel` to the command center
- Show available now, occupied now, overflow waiting, and zone-level availability
- Add quick filters that drive the existing ICU heatmap
- Keep the feature inside the current command-center page and component model
- Add focused frontend tests and verify build/runtime behavior

## Out of Scope

- New backend endpoints
- New persistence model for room state
- Predictive "available soon" timelines
- Non-ICU room classes beyond the current live ICU map

## Implementation Plan

### Task 1: Create the room-availability panel

**Files:**
- Create: `frontend/src/components/RoomAvailabilityPanel.tsx`
- Test: `frontend/src/components/RoomAvailabilityPanel.test.tsx`

**Steps:**
1. Create a presentational panel that accepts `beds`, `triageQueue`, `selectedAvailability`, `selectedZone`, and change callbacks.
2. Compute:
   - available count
   - occupied count
   - overflow count
   - zone-level availability summaries
   - available bed IDs for quick operator scan
3. Render compact summary metrics plus filter buttons:
   - `All beds`
   - `Available now`
   - `Occupied only`
   - zone filters using the live zone names from the data
4. Add a focused component test covering:
   - live counts
   - available bed labels
   - filter callback behavior

### Task 2: Wire the feature into the command center

**Files:**
- Modify: `frontend/src/pages/CommandCenter.tsx`

**Steps:**
1. Add local state for:
   - `availabilityFilter: 'all' | 'available' | 'occupied'`
   - `selectedZone: string | null`
2. Place `RoomAvailabilityPanel` directly above the ICU heatmap in the left dashboard column so it reads as the control surface for the map.
3. Pass the current filters into the heatmap.
4. Keep the existing command-center bento layout intact.

### Task 3: Add heatmap filtering support

**Files:**
- Modify: `frontend/src/components/ICUBedHeatmap.tsx`

**Steps:**
1. Extend the component props to accept `availabilityFilter` and `selectedZone`.
2. Filter visible bed tiles from the live data before rendering.
3. Keep the top chip counts based on the full source data, not the filtered subset, so operators always see true system totals.
4. Add an empty-state message when a filter produces no matching beds.
5. Preserve triage queue visibility, but allow the new panel to signal overflow pressure separately.

### Task 4: Validate typing and UI consistency

**Files:**
- Modify only if needed: `frontend/src/types/index.ts`
- Modify only if needed: `frontend/src/styles/index.css`

**Steps:**
1. Add shared filter types only if duplication starts to spread.
2. Reuse existing shell/card/chip styles before adding new CSS.
3. Keep the panel visually consistent in both light and dark mode.

## Verification

- `npm run test:run`
- `npm run build`
- Browser verification on `http://localhost:3000`
- Confirm:
  - panel renders live counts
  - filters update the heatmap
  - dark mode styling remains consistent
  - no layout regressions on the left command column
