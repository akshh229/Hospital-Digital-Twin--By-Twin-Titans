import { useEffect, useMemo, useState } from 'react'
import type { SimulationControlRequest, SimulationState } from '../types'

interface SimulationControlPanelProps {
  simulation: SimulationState
  isPending: boolean
  onControl: (payload: SimulationControlRequest) => void
}

const scenarioOptions = [
  {
    id: 'surge_admissions',
    label: 'Surge admissions',
    description: 'Stress bed allocation with sudden incoming demand.',
  },
  {
    id: 'oxygen_shortage',
    label: 'Oxygen shortage',
    description: 'Force resource pressure through respiratory instability.',
  },
  {
    id: 'acuity_cluster',
    label: 'High-acuity cluster',
    description: 'Push multiple unstable patients into the ICU at once.',
  },
] as const

const severityOptions = ['minor', 'major', 'extreme'] as const
const speedOptions = [1, 1.5, 2, 3] as const

export default function SimulationControlPanel({
  simulation,
  isPending,
  onControl,
}: SimulationControlPanelProps) {
  const [scenario, setScenario] = useState(simulation.active_scenario || 'surge_admissions')
  const [severity, setSeverity] = useState<'minor' | 'major' | 'extreme'>('major')
  const activeInterventions = simulation.active_interventions ?? []

  useEffect(() => {
    if (simulation.active_scenario && simulation.active_scenario !== 'baseline') {
      setScenario(simulation.active_scenario)
    }
  }, [simulation.active_scenario])

  const scenarioDescription = useMemo(
    () =>
      scenarioOptions.find((option) => option.id === scenario)?.description ??
      'Adjust the live ICU state with a scripted crisis scenario.',
    [scenario]
  )

  return (
    <section className="card space-y-5">
      <div>
        <p className="section-label">Simulation control panel</p>
        <h2 className="mt-2 font-display text-[2rem] font-semibold leading-none tracking-[-0.03em] text-lazarus-text">
          Scenario command
        </h2>
        <p className="mt-3 text-sm leading-6 text-lazarus-muted">
          Pause the twin, increase playback speed, or inject a scripted ICU crisis
          to demonstrate automated routing under duress.
        </p>
      </div>

      <div className="rounded-[1.5rem] border border-lazarus-border/80 bg-lazarus-surface/80 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-lazarus-muted">
              Current mode
            </p>
            <p className="mt-2 text-lg font-semibold text-lazarus-text">
              {simulation.crisis_label}
            </p>
            <p className="mt-1 text-sm text-lazarus-muted">
              Speed {simulation.speed.toFixed(1)}x • Virtual admissions {simulation.virtual_admissions}
            </p>
          </div>
          <span
            className={`rounded-full px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] ${
              simulation.is_paused
                ? 'bg-lazarus-warning/12 text-lazarus-warning'
                : 'bg-lazarus-normal/12 text-lazarus-normal'
            }`}
          >
            {simulation.is_paused ? 'Paused' : 'Live'}
          </span>
        </div>
      </div>

      <div className="rounded-[1.5rem] border border-lazarus-border/80 bg-lazarus-surface/65 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="section-label">Active interventions</p>
            <p className="mt-2 text-sm leading-6 text-lazarus-muted">
              {activeInterventions.length > 0
                ? 'These operator actions are currently shifting the live ICU model.'
                : 'No intervention controls are currently engaged.'}
            </p>
          </div>
          <span className="rounded-full bg-lazarus-info/12 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-lazarus-info">
            {activeInterventions.length} active
          </span>
        </div>

        {activeInterventions.length > 0 ? (
          <div className="mt-4 grid gap-3">
            {activeInterventions.map((intervention) => (
              <div
                key={intervention.id}
                className="rounded-[1.2rem] border border-lazarus-info/18 bg-lazarus-info/6 p-3"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <p className="text-sm font-semibold text-lazarus-text">
                    {intervention.label}
                  </p>
                  <span className="rounded-full bg-lazarus-info/14 px-2.5 py-1 text-[0.7rem] font-semibold uppercase tracking-[0.16em] text-lazarus-info">
                    {intervention.value}
                  </span>
                </div>
                <p className="mt-2 text-xs leading-5 text-lazarus-muted">
                  {intervention.effect}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {intervention.can_step_down ? (
                    <button
                      type="button"
                      className="rounded-full border border-lazarus-warning/30 bg-lazarus-warning/10 px-3 py-1.5 text-xs font-semibold text-lazarus-warning transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
                      disabled={isPending}
                      onClick={() =>
                        onControl({
                          action: 'step_down_intervention',
                          intervention_id: intervention.id,
                        })
                      }
                    >
                      {isPending
                        ? 'Updating intervention...'
                        : intervention.step_down_label ?? 'Step down'}
                    </button>
                  ) : null}
                  {intervention.can_clear ? (
                    <button
                      type="button"
                      className="rounded-full border border-lazarus-border bg-lazarus-surface px-3 py-1.5 text-xs font-semibold text-lazarus-text transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
                      disabled={isPending}
                      onClick={() =>
                        onControl({
                          action: 'clear_intervention',
                          intervention_id: intervention.id,
                        })
                      }
                    >
                      {isPending
                        ? 'Updating intervention...'
                        : intervention.clear_label ?? 'Clear intervention'}
                    </button>
                  ) : null}
                </div>
              </div>
            ))}
          </div>
        ) : null}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <button
          type="button"
          className="btn-primary w-full disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isPending}
          onClick={() =>
            onControl({ action: simulation.is_paused ? 'resume' : 'pause' })
          }
        >
          {simulation.is_paused ? 'Resume Twin' : 'Pause Twin'}
        </button>
        <button
          type="button"
          className="rounded-full border border-lazarus-border bg-lazarus-surface px-5 py-2.5 font-semibold text-lazarus-text transition-all hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isPending}
          onClick={() => onControl({ action: 'reset' })}
        >
          Reset Baseline
        </button>
      </div>

      <div className="space-y-3">
        <div>
          <p className="section-label">Playback speed</p>
          <p className="mt-1 text-sm text-lazarus-muted">
            Accelerate the scenario to show future pressure faster.
          </p>
        </div>
        <div className="grid grid-cols-4 gap-2">
          {speedOptions.map((speed) => {
            const active = Math.abs(simulation.speed - speed) < 0.01
            return (
              <button
                key={speed}
                type="button"
                className={`rounded-full border px-3 py-2 text-sm font-semibold transition-transform hover:-translate-y-0.5 ${
                  active
                    ? 'border-lazarus-info bg-lazarus-info/12 text-lazarus-info'
                    : 'border-lazarus-border bg-lazarus-surface text-lazarus-text'
                }`}
                disabled={isPending}
                onClick={() => onControl({ action: 'set_speed', speed })}
              >
                {speed}x
              </button>
            )
          })}
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <p className="section-label">Crisis scenario</p>
          <p className="mt-1 text-sm text-lazarus-muted">{scenarioDescription}</p>
        </div>
        <div className="grid gap-2">
          {scenarioOptions.map((option) => (
            <button
              key={option.id}
              type="button"
              className={`rounded-[1.2rem] border px-4 py-3 text-left transition-transform hover:-translate-y-0.5 ${
                scenario === option.id
                  ? 'border-lazarus-info bg-lazarus-info/10'
                  : 'border-lazarus-border bg-lazarus-surface/75'
              }`}
              onClick={() => setScenario(option.id)}
            >
              <p className="text-sm font-semibold text-lazarus-text">{option.label}</p>
              <p className="mt-1 text-xs leading-5 text-lazarus-muted">{option.description}</p>
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        <div>
          <p className="section-label">Severity</p>
          <p className="mt-1 text-sm text-lazarus-muted">
            Scale the crisis from a warning drill to a full command-room stress case.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-2">
          {severityOptions.map((option) => (
            <button
              key={option}
              type="button"
              className={`rounded-full border px-3 py-2 text-sm font-semibold capitalize transition-transform hover:-translate-y-0.5 ${
                severity === option
                  ? 'border-lazarus-warning bg-lazarus-warning/12 text-lazarus-warning'
                  : 'border-lazarus-border bg-lazarus-surface text-lazarus-text'
              }`}
              onClick={() => setSeverity(option)}
            >
              {option}
            </button>
          ))}
        </div>
      </div>

      <button
        type="button"
        className="w-full rounded-[1.4rem] border border-lazarus-critical/25 bg-lazarus-critical/10 px-5 py-4 text-left transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
        disabled={isPending}
        onClick={() =>
          onControl({
            action: 'inject_crisis',
            scenario,
            severity,
          })
        }
      >
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-lazarus-critical">
          Inject crisis
        </p>
        <p className="mt-2 text-base font-semibold text-lazarus-text">
          Launch {scenarioOptions.find((option) => option.id === scenario)?.label}
        </p>
        <p className="mt-2 text-sm leading-6 text-lazarus-muted">
          Apply a {severity} severity stress scenario and let the ward allocator respond in realtime.
        </p>
      </button>
    </section>
  )
}
