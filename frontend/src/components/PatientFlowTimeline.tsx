import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import type { IncidentReplayFrame, TimelineEvent } from '../types'

interface PatientFlowTimelineProps {
  timeline: TimelineEvent[]
  replayFrames: IncidentReplayFrame[]
}

function toneForSeverity(severity: TimelineEvent['severity']) {
  if (severity === 'critical') {
    return {
      dot: 'bg-lazarus-critical',
      badge: 'bg-lazarus-critical/10 text-lazarus-critical',
      border: 'border-lazarus-critical/18',
    }
  }

  if (severity === 'warning') {
    return {
      dot: 'bg-lazarus-warning',
      badge: 'bg-lazarus-warning/10 text-lazarus-warning',
      border: 'border-lazarus-warning/18',
    }
  }

  return {
    dot: 'bg-lazarus-normal',
    badge: 'bg-lazarus-normal/10 text-lazarus-normal',
    border: 'border-lazarus-normal/18',
  }
}

function formatTimestamp(timestamp: string) {
  return new Date(timestamp).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })
}

export default function PatientFlowTimeline({
  timeline,
  replayFrames,
}: PatientFlowTimelineProps) {
  const [activeFrameIndex, setActiveFrameIndex] = useState(0)
  const activeFrame = replayFrames[activeFrameIndex]
  const relatedEventIds = useMemo(
    () => new Set(replayFrames.slice(1).map((frame) => frame.id.replace('replay-', ''))),
    [replayFrames]
  )

  return (
    <section className="card space-y-5">
      <div>
        <p className="section-label">Patient flow timeline</p>
        <h2 className="mt-2 font-display text-[2rem] font-semibold leading-none tracking-[-0.03em] text-lazarus-text">
          Live command events
        </h2>
        <p className="mt-3 text-sm leading-6 text-lazarus-muted">
          Admissions, routing decisions, alert escalations, and simulation interventions
          appear here in the order your operations team would feel them.
        </p>
      </div>

      {activeFrame ? (
        <div className="rounded-[1.5rem] border border-lazarus-border/70 bg-lazarus-surface/80 p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                Incident replay
              </p>
              <h3 className="mt-2 text-lg font-semibold text-lazarus-text">
                {activeFrame.phase_label} • {activeFrame.title}
              </h3>
              <p className="mt-2 text-sm leading-6 text-lazarus-muted">
                {activeFrame.summary}
              </p>
            </div>
            <span className="dossier-chip">
              Reconstructed checkpoint
            </span>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-[1.2rem] bg-lazarus-surface/85 px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                ICU occupied
              </p>
              <p className="mt-1 font-mono text-xl font-semibold text-lazarus-text">
                {activeFrame.icu_occupied}
              </p>
            </div>
            <div className="rounded-[1.2rem] bg-lazarus-surface/85 px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                Overflow
              </p>
              <p className="mt-1 font-mono text-xl font-semibold text-lazarus-text">
                {activeFrame.overflow_patients}
              </p>
            </div>
            <div className="rounded-[1.2rem] bg-lazarus-surface/85 px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                Alerts
              </p>
              <p className="mt-1 font-mono text-xl font-semibold text-lazarus-text">
                {activeFrame.active_alerts}
              </p>
            </div>
            <div className="rounded-[1.2rem] bg-lazarus-surface/85 px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                Attention set
              </p>
              <p className="mt-1 font-mono text-xl font-semibold text-lazarus-text">
                {activeFrame.attention_patients}
              </p>
            </div>
          </div>

          <p className="mt-4 text-sm leading-6 text-lazarus-muted">
            {activeFrame.focus_note}
          </p>

          {replayFrames.length > 1 ? (
            <div className="mt-4 space-y-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                  Replay scrubber
                </p>
                <span className="text-xs text-lazarus-muted">
                  {activeFrameIndex + 1} / {replayFrames.length}
                </span>
              </div>
              <input
                type="range"
                min={0}
                max={replayFrames.length - 1}
                value={activeFrameIndex}
                onChange={(event) => setActiveFrameIndex(Number(event.target.value))}
                className="w-full accent-lazarus-info"
              />
              <p className="text-xs leading-5 text-lazarus-muted">
                Replay checkpoints are reconstructed from the current event stream to help demo
                the shape of the incident as it unfolded.
              </p>
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="relative pl-5">
        <div className="absolute bottom-0 left-[0.4rem] top-0 w-px bg-lazarus-border/80" />
        <div className="space-y-4">
          {timeline.map((event) => {
            const tone = toneForSeverity(event.severity)

            return (
              <div
                key={event.id}
                className={`relative rounded-[1.35rem] border bg-lazarus-surface/85 p-4 ${tone.border} ${
                  relatedEventIds.has(event.id) ? 'ring-1 ring-lazarus-info/20' : ''
                }`}
              >
                <span
                  className={`absolute left-[-1.12rem] top-5 h-3 w-3 rounded-full ring-4 ring-lazarus-bg ${tone.dot}`}
                  aria-hidden="true"
                />
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-lazarus-text">{event.title}</p>
                    <p className="mt-1 text-xs uppercase tracking-[0.2em] text-lazarus-muted">
                      {event.event_type} • {formatTimestamp(event.timestamp)}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] ${tone.badge}`}
                  >
                    {event.severity}
                  </span>
                </div>

                <p className="mt-3 text-sm leading-6 text-lazarus-muted">
                  {event.description}
                </p>

                {(event.patient_id || event.bed_id) && (
                  <div className="mt-3 flex flex-wrap gap-2">
                    {event.bed_id && <span className="dossier-chip">{event.bed_id}</span>}
                    {event.patient_id && (
                      <Link to={`/patient/${event.patient_id}`} className="dossier-chip">
                        Open patient view
                      </Link>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
