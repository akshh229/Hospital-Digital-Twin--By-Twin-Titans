# Round 2 Demo Playbook

## Product Story

St. Jude ICU Digital Twin simulates hospital logistics under duress.
The demo should show how live telemetry, risk scoring, ward allocation, and
resource forecasting work together inside one command surface.

## Recommended Demo Flow

1. Start on the command center homepage.
   Point out ICU occupancy, overflow, active alerts, and average risk.

2. Open the live ICU bed heatmap.
   Explain that beds are assigned by calculated risk score and alert pressure.

3. Run one of the one-click playbooks.
   Use the playbook cards in the right column for a faster demo.

4. Watch the resource graph and timeline react.
   Call out how the forecast changes as the simulator stress increases.

5. Click into one patient from the bed heatmap or timeline.
   Show the patient drill-down, command snapshot, alert state, and telemetry lane.

## Best Playbooks

### Surge Response Drill

- Use when:
  You want to show overflow and routing pressure quickly.
- Best talking point:
  "The allocator fills ICU beds first, then surfaces queue pressure when demand exceeds live capacity."

### Respiratory Supply Failure

- Use when:
  You want the strongest resource-consumption story.
- Best talking point:
  "The digital twin predicts oxygen and ventilator pressure before the team is fully underwater."

### High-Acuity Cluster

- Use when:
  You want to highlight prioritization and critical triage.
- Best talking point:
  "The system reorders bed assignment around the sickest patients first."

## Safe Reset Path

If the demo becomes too noisy:

1. Click `Reset Baseline`
2. Set playback speed back to `1.0x`
3. Re-run the desired playbook

## Patient Drill-Down Talking Points

- Command snapshot:
  Shows where the patient sits in the live routing model.
- Active escalation:
  Shows whether the patient is currently part of the alert queue.
- Telemetry lane:
  Shows the bedside signal trend behind the risk score.
- Medication schedule view:
  Shows treatment context alongside vitals.
