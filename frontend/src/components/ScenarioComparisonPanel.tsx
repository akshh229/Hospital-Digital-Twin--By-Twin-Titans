import type { ScenarioComparison, ScenarioDeltaMetric } from '../types'

interface ScenarioComparisonPanelProps {
  comparison: ScenarioComparison
}

function toneForStatus(status: ScenarioDeltaMetric['status']) {
  if (status === 'degraded') {
    return 'border-lazarus-critical/25 bg-lazarus-critical/8'
  }
  if (status === 'improved') {
    return 'border-lazarus-normal/25 bg-lazarus-normal/8'
  }
  return 'border-lazarus-border/70 bg-lazarus-surface/75'
}

function formatDelta(metric: ScenarioDeltaMetric) {
  if (metric.delta === 0) {
    return 'No change'
  }

  const sign = metric.delta > 0 ? '+' : ''
  return `${sign}${metric.delta}`
}

function ComparisonGrid({
  title,
  metrics,
}: {
  title: string
  metrics: ScenarioDeltaMetric[]
}) {
  return (
    <div className="space-y-3">
      <p className="section-label">{title}</p>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {metrics.map((metric) => (
          <div
            key={metric.key}
            className={`rounded-[1.35rem] border p-4 ${toneForStatus(metric.status)}`}
          >
            <p className="text-sm font-semibold text-lazarus-text">{metric.label}</p>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                  Baseline
                </p>
                <p className="mt-1 font-mono text-lg font-semibold text-lazarus-text">
                  {metric.baseline_value}
                </p>
              </div>
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                  Current
                </p>
                <p className="mt-1 font-mono text-lg font-semibold text-lazarus-text">
                  {metric.current_value}
                </p>
              </div>
            </div>
            <div className="mt-3 flex items-center justify-between gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-lazarus-muted">
                Delta
              </span>
              <span
                className={`rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] ${
                  metric.status === 'degraded'
                    ? 'bg-lazarus-critical/12 text-lazarus-critical'
                    : metric.status === 'improved'
                      ? 'bg-lazarus-normal/12 text-lazarus-normal'
                      : 'bg-lazarus-surface text-lazarus-muted'
                }`}
              >
                {formatDelta(metric)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default function ScenarioComparisonPanel({
  comparison,
}: ScenarioComparisonPanelProps) {
  return (
    <section className="card space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="section-label">Scenario compare mode</p>
          <h2 className="mt-2 font-display text-[2rem] font-semibold leading-none tracking-[-0.03em] text-lazarus-text">
            Baseline vs current pressure
          </h2>
          <p className="mt-3 max-w-3xl text-sm leading-6 text-lazarus-muted">
            This compare view uses the same patient cohort under baseline assumptions and the
            current crisis state, so reviewers can see what the scenario is actually changing.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="dossier-chip">{comparison.baseline_label}</span>
          <span className="dossier-chip">{comparison.current_label}</span>
        </div>
      </div>

      <ComparisonGrid title="Summary deltas" metrics={comparison.summary_metrics} />
      <ComparisonGrid title="Resource deltas" metrics={comparison.resource_metrics} />
    </section>
  )
}
