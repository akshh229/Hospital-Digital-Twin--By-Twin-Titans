import type { SimulationControlRequest, SimulationState } from '../types'

interface ScenarioPlaybooksPanelProps {
  simulation: SimulationState
  isPending: boolean
  onRunPlaybook: (playbook: ScenarioPlaybook) => void | Promise<void>
}

export interface ScenarioPlaybook {
  id: string
  title: string
  summary: string
  scenario: NonNullable<SimulationControlRequest['scenario']>
  severity: NonNullable<SimulationControlRequest['severity']>
  speed: number
  patientCount: number
  expectedOutcome: string
}

const playbooks: ScenarioPlaybook[] = [
  {
    id: 'surge-response',
    title: 'Surge Response Drill',
    summary: 'Simulate a sudden wave of incoming patients to stress bed assignment and overflow handling.',
    scenario: 'surge_admissions',
    severity: 'major',
    speed: 1.5,
    patientCount: 4,
    expectedOutcome: 'Overflow queue grows, allocator fills ICU beds, and the timeline shows routing pressure.',
  },
  {
    id: 'oxygen-collapse',
    title: 'Respiratory Supply Failure',
    summary: 'Drive respiratory instability and oxygen depletion to show resource forecasting under duress.',
    scenario: 'oxygen_shortage',
    severity: 'extreme',
    speed: 2,
    patientCount: 5,
    expectedOutcome: 'Oxygen reserve falls sharply, alert count rises, and respiratory demand dominates the graphs.',
  },
  {
    id: 'acuity-cluster',
    title: 'High-Acuity Cluster',
    summary: 'Force multiple unstable patients into the same time window to demonstrate triage prioritization.',
    scenario: 'acuity_cluster',
    severity: 'major',
    speed: 1.5,
    patientCount: 4,
    expectedOutcome: 'Critical patients take the hottest beds first and the flow timeline becomes visibly more urgent.',
  },
]

export default function ScenarioPlaybooksPanel({
  simulation,
  isPending,
  onRunPlaybook,
}: ScenarioPlaybooksPanelProps) {
  return (
    <section className="card space-y-5">
      <div>
        <p className="section-label">Demo playbooks</p>
        <h2 className="mt-2 font-display text-[2rem] font-semibold leading-none tracking-[-0.03em] text-lazarus-text">
          One-click storylines
        </h2>
        <p className="mt-3 text-sm leading-6 text-lazarus-muted">
          These preset runs make your live demo smoother by pairing a scenario, severity,
          playback speed, and patient load into a single action.
        </p>
      </div>

      <div className="space-y-3">
        {playbooks.map((playbook) => (
          <div
            key={playbook.id}
            className="rounded-[1.4rem] border border-lazarus-border/70 bg-lazarus-surface/75 p-4"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="max-w-xl">
                <p className="text-sm font-semibold text-lazarus-text">{playbook.title}</p>
                <p className="mt-1 text-sm leading-6 text-lazarus-muted">
                  {playbook.summary}
                </p>
              </div>
              <button
                type="button"
                disabled={isPending}
                onClick={() => onRunPlaybook(playbook)}
                className="rounded-full border border-lazarus-info bg-lazarus-info/10 px-4 py-2 text-sm font-semibold text-lazarus-info transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Run playbook
              </button>
            </div>

            <div className="mt-3 flex flex-wrap gap-2">
              <span className="dossier-chip">{playbook.severity} severity</span>
              <span className="dossier-chip">{playbook.speed.toFixed(1)}x speed</span>
              <span className="dossier-chip">{playbook.patientCount} affected patients</span>
              {simulation.active_scenario === playbook.scenario && (
                <span className="dossier-chip">Live scenario</span>
              )}
            </div>

            <div className="mt-3 rounded-[1.2rem] bg-lazarus-surface/80 px-4 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                Expected outcome
              </p>
              <p className="mt-2 text-sm leading-6 text-lazarus-muted">
                {playbook.expectedOutcome}
              </p>
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
