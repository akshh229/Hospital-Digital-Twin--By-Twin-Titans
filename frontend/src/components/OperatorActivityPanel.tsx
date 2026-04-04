import type { OperatorActivityEntry, SimulationState } from '../types'

interface OperatorActivityPanelProps {
  simulation: SimulationState
  activity: OperatorActivityEntry[]
}

function toneForSeverity(severity: OperatorActivityEntry['severity']) {
  if (severity === 'critical') {
    return {
      badge: 'badge-critical',
      border: 'border-lazarus-critical/20',
    }
  }

  if (severity === 'warning') {
    return {
      badge: 'badge-warning',
      border: 'border-lazarus-warning/20',
    }
  }

  return {
    badge: 'badge-normal',
    border: 'border-lazarus-normal/20',
  }
}

function formatTimestamp(timestamp?: string | null) {
  if (!timestamp) {
    return 'No operator action recorded yet'
  }

  return new Date(timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  })
}

function formatIntervention(interventionId?: string | null) {
  if (!interventionId) {
    return null
  }

  const labels: Record<string, string> = {
    'open-surge-beds': 'Surge beds',
    'protect-oxygen-reserve': 'Oxygen reserve',
    'rebalance-nurse-coverage': 'Staff reinforcement',
    'review-alerting-patients': 'Alert review',
  }

  return labels[interventionId] ?? interventionId.replace(/-/g, ' ')
}

export default function OperatorActivityPanel({
  simulation,
  activity,
}: OperatorActivityPanelProps) {
  const latestAction = activity[0]
  const activeInterventionCount = simulation.active_interventions.length

  return (
    <section className="card space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="section-label">Operator activity</p>
          <h2 className="mt-2 font-display text-[2rem] font-semibold leading-none tracking-[-0.03em] text-lazarus-text">
            Command audit trail
          </h2>
          <p className="mt-3 text-sm leading-6 text-lazarus-muted">
            Recent simulator actions, intervention changes, and crisis injections are
            tracked here so the team can explain how the ICU posture was changed.
          </p>
        </div>
        <span className={simulation.is_paused ? 'badge-warning' : 'badge-normal'}>
          {simulation.is_paused ? 'Simulator paused' : 'Simulator running'}
        </span>
      </div>

      <div className="rounded-[1.45rem] border border-lazarus-border/70 bg-lazarus-surface/80 p-4">
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
          Latest operator posture
        </p>
        <div className="mt-3 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h3 className="text-lg font-semibold text-lazarus-text">
              {simulation.last_action_label}
            </h3>
            <p className="mt-2 text-sm leading-6 text-lazarus-muted">
              Current scenario is {simulation.crisis_label.toLowerCase()} with playback at{' '}
              {simulation.speed.toFixed(1)}x.
            </p>
          </div>
          <span className="dossier-chip">{formatTimestamp(simulation.last_action_at)}</span>
        </div>

        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <div className="rounded-[1.2rem] bg-lazarus-surface/85 px-4 py-3">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
              Active interventions
            </p>
            <p className="mt-1 font-mono text-xl font-semibold text-lazarus-text">
              {activeInterventionCount}
            </p>
          </div>
          <div className="rounded-[1.2rem] bg-lazarus-surface/85 px-4 py-3">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
              Playback speed
            </p>
            <p className="mt-1 font-mono text-xl font-semibold text-lazarus-text">
              {simulation.speed.toFixed(1)}x
            </p>
          </div>
          <div className="rounded-[1.2rem] bg-lazarus-surface/85 px-4 py-3">
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
              Scenario
            </p>
            <p className="mt-1 text-sm font-semibold text-lazarus-text">
              {simulation.crisis_label}
            </p>
          </div>
        </div>
      </div>

      {activity.length > 0 ? (
        <div className="space-y-3">
          {activity.map((entry) => {
            const tone = toneForSeverity(entry.severity)
            const interventionLabel = formatIntervention(entry.intervention_id)

            return (
              <article
                key={entry.id}
                className={`rounded-[1.35rem] border bg-lazarus-surface/80 p-4 ${tone.border}`}
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-lazarus-text">
                      {entry.action_label}
                    </p>
                    <p className="mt-1 text-xs uppercase tracking-[0.18em] text-lazarus-muted">
                      {entry.event_type} • {formatTimestamp(entry.timestamp)}
                    </p>
                  </div>
                  <span className={tone.badge}>{entry.severity}</span>
                </div>

                <p className="mt-3 text-sm leading-6 text-lazarus-muted">
                  {entry.description}
                </p>

                <div className="mt-3 flex flex-wrap gap-2">
                  <span className="dossier-chip">{entry.title}</span>
                  {interventionLabel ? (
                    <span className="dossier-chip">{interventionLabel}</span>
                  ) : null}
                  {entry.scenario_label ? (
                    <span className="dossier-chip">{entry.scenario_label}</span>
                  ) : null}
                  {entry.speed != null ? (
                    <span className="dossier-chip">{entry.speed.toFixed(1)}x</span>
                  ) : null}
                </div>
              </article>
            )
          })}
        </div>
      ) : (
        <div className="rounded-[1.35rem] border border-dashed border-lazarus-border/80 bg-lazarus-surface/65 p-4">
          <p className="text-sm leading-6 text-lazarus-muted">
            Operator actions will appear here once the command team pauses, resumes,
            injects a scenario, or changes intervention posture.
          </p>
        </div>
      )}

      {latestAction ? (
        <p className="text-xs leading-5 text-lazarus-muted">
          Latest logged action: {latestAction.action_label}. Keep this panel open during
          demos to narrate exactly how the command team changed the twin.
        </p>
      ) : null}
    </section>
  )
}
