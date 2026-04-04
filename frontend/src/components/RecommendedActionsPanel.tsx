import type { RecommendedAction } from '../types'

interface RecommendedActionsPanelProps {
  actions: RecommendedAction[]
  isPending: boolean
  onExecuteAction: (action: RecommendedAction) => void
}

function toneForPriority(priority: RecommendedAction['priority']) {
  if (priority === 'critical') {
    return 'badge-critical'
  }
  if (priority === 'warning') {
    return 'badge-warning'
  }
  return 'badge-normal'
}

function formatProjectedMetric(metric: RecommendedAction['projected_metrics'][number]) {
  const current = formatMetricValue(metric.current_value, metric.unit)
  const projected = formatMetricValue(metric.projected_value, metric.unit)

  return `${metric.label}: ${current} -> ${projected}`
}

function formatObservedMetric(metric: RecommendedAction['observed_metrics'][number]) {
  const baseline = formatMetricValue(metric.baseline_value, metric.unit)
  const current = formatMetricValue(metric.current_value, metric.unit)

  return `${metric.label}: ${baseline} -> ${current}`
}

function formatMetricValue(value: number, unit: string) {
  if (unit === '%') {
    return `${value}%`
  }

  if (unit === 'patients' || unit === 'alerts' || unit === 'staff' || unit === 'beds') {
    return `${value}`
  }

  return `${value}${unit}`
}

function toneForState(state: RecommendedAction['state']) {
  if (state === 'saturated') {
    return 'rounded-full bg-lazarus-warning/12 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-lazarus-warning'
  }
  if (state === 'active' || state === 'recently_applied') {
    return 'rounded-full bg-lazarus-info/12 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-lazarus-info'
  }
  return 'rounded-full bg-lazarus-normal/12 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-lazarus-normal'
}

export default function RecommendedActionsPanel({
  actions,
  isPending,
  onExecuteAction,
}: RecommendedActionsPanelProps) {
  return (
    <section className="card space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="section-label">Recommended next actions</p>
          <h2 className="mt-2 font-display text-[2rem] font-semibold leading-none tracking-[-0.03em] text-lazarus-text">
            Ops guidance
          </h2>
        </div>
        <span className="dossier-chip">Top {actions.length} priorities</span>
      </div>

      {actions.length > 0 ? (
        <div className="space-y-3">
          {actions.map((action, index) => (
            <div
              key={action.id}
              className="rounded-[1.35rem] border border-lazarus-border/70 bg-lazarus-surface/75 p-4"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                    Action {index + 1}
                  </p>
                  <p className="mt-2 text-base font-semibold text-lazarus-text">
                    {action.title}
                  </p>
                </div>
                <div className="flex flex-wrap items-center justify-end gap-2">
                  <span className={toneForPriority(action.priority)}>{action.priority}</span>
                  <span className={toneForState(action.state)}>{action.state_label}</span>
                </div>
              </div>

              <p className="mt-3 text-sm leading-6 text-lazarus-muted">{action.rationale}</p>
              <p className="mt-3 text-xs leading-5 text-lazarus-muted">{action.state_reason}</p>

              <div
                className={`mt-4 grid gap-3 ${
                  action.observed_summary || action.observed_metrics.length > 0
                    ? 'xl:grid-cols-2'
                    : ''
                }`}
              >
                <div className="rounded-[1.2rem] border border-lazarus-border/70 bg-lazarus-surface/80 px-4 py-3">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                      Projected {action.projected_window_minutes}-minute effect
                    </p>
                    <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-lazarus-info">
                      Modeled
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-lazarus-text">
                    {action.projected_summary}
                  </p>
                  {action.projected_metrics.length > 0 ? (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {action.projected_metrics.slice(0, 2).map((metric) => (
                        <span
                          key={metric.key}
                          className="rounded-full border border-lazarus-border/70 bg-lazarus-surface px-2.5 py-1 text-[11px] leading-5 text-lazarus-muted"
                        >
                          {formatProjectedMetric(metric)}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>

                {action.observed_summary || action.observed_metrics.length > 0 ? (
                  <div className="rounded-[1.2rem] border border-lazarus-info/18 bg-lazarus-info/6 px-4 py-3">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                        Observed after latest operator action
                      </p>
                      <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-lazarus-info">
                        Live
                      </span>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-lazarus-text">
                      {action.observed_summary}
                    </p>
                    {action.observed_metrics.length > 0 ? (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {action.observed_metrics.slice(0, 2).map((metric) => (
                          <span
                            key={metric.key}
                            className="rounded-full border border-lazarus-info/20 bg-lazarus-surface px-2.5 py-1 text-[11px] leading-5 text-lazarus-muted"
                          >
                            {formatObservedMetric(metric)}
                          </span>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ) : null}
              </div>

              <p className="mt-3 text-[11px] font-semibold uppercase tracking-[0.16em] text-lazarus-muted">
                Suggested owner: {action.owner}
              </p>

              {action.action_type === 'advisory' ? (
                <div className="mt-4 rounded-[1rem] border border-lazarus-border/70 bg-lazarus-surface/70 px-4 py-3 text-sm text-lazarus-muted">
                  Advisory only. This item is guidance for the operator and does not trigger a simulator-side change.
                </div>
              ) : (
                <button
                  type="button"
                  className="mt-4 rounded-full border border-lazarus-info bg-lazarus-info/10 px-4 py-2 text-sm font-semibold text-lazarus-info transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
                  disabled={isPending || !action.can_apply}
                  onClick={() => onExecuteAction(action)}
                >
                  {isPending
                    ? 'Applying recommendation...'
                    : action.can_apply
                      ? action.apply_label ?? 'Run action'
                      : 'Unavailable'}
                </button>
              )}
            </div>
          ))}
        </div>
      ) : (
        <div className="rounded-[1.35rem] border border-lazarus-border/70 bg-lazarus-surface/75 p-4 text-sm text-lazarus-muted">
          No immediate intervention is required. Continue monitored ICU routing.
        </div>
      )}
    </section>
  )
}
