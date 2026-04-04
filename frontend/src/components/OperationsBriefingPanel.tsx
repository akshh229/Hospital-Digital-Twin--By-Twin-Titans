import type { OperationsBriefing, OperationsTrust } from '../types'

interface OperationsBriefingPanelProps {
  briefing: OperationsBriefing
  trust: OperationsTrust
}

function toneForTelemetry(state: OperationsTrust['telemetry_state']) {
  if (state === 'paused') {
    return 'badge-warning'
  }
  if (state === 'watch') {
    return 'badge-warning'
  }
  return 'badge-normal'
}

function toneForConfidence(label: OperationsTrust['confidence_label']) {
  if (label === 'low') {
    return 'badge-critical'
  }
  if (label === 'medium') {
    return 'badge-warning'
  }
  return 'badge-normal'
}

function formatFreshness(seconds: number | null) {
  if (seconds == null) {
    return 'Awaiting fresh vitals'
  }

  if (seconds < 60) {
    return `Updated ${seconds}s ago`
  }

  const minutes = Math.floor(seconds / 60)
  return `Updated ${minutes}m ago`
}

export default function OperationsBriefingPanel({
  briefing,
  trust,
}: OperationsBriefingPanelProps) {
  return (
    <section className="card space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="section-label">What changed in the last 15 minutes</p>
          <h2 className="mt-2 font-display text-[2rem] font-semibold leading-none tracking-[-0.03em] text-lazarus-text">
            {briefing.headline}
          </h2>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className={toneForTelemetry(trust.telemetry_state)}>
            {trust.telemetry_state === 'live'
              ? 'Live telemetry'
              : trust.telemetry_state === 'paused'
                ? 'Paused snapshot'
                : 'Feed watch'}
          </span>
          <span className={toneForConfidence(trust.confidence_label)}>
            {trust.confidence_label} confidence
          </span>
        </div>
      </div>

      <p className="text-sm leading-6 text-lazarus-muted">{briefing.summary}</p>

      <div className="flex flex-wrap gap-2">
        <span className="dossier-chip">{trust.data_source}</span>
        <span className="dossier-chip">{formatFreshness(trust.telemetry_age_seconds)}</span>
        {trust.last_telemetry_at && (
          <span className="dossier-chip">
            Last signal{' '}
            {new Date(trust.last_telemetry_at).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit',
            })}
          </span>
        )}
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        {briefing.changes.map((change, index) => (
          <div
            key={`${change}-${index}`}
            className="rounded-[1.35rem] border border-lazarus-border/70 bg-lazarus-surface/75 p-4"
          >
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
              Change {index + 1}
            </p>
            <p className="mt-2 text-sm leading-6 text-lazarus-text">{change}</p>
          </div>
        ))}
      </div>

      <div className="rounded-[1.35rem] border border-lazarus-border/70 bg-lazarus-surface/75 p-4">
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
          Trust note
        </p>
        <p className="mt-2 text-sm leading-6 text-lazarus-muted">
          {trust.confidence_reason}
        </p>
      </div>
    </section>
  )
}
