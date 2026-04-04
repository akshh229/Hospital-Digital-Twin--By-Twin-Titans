import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import { useOperationsOverview } from '../hooks/useOperations'

interface PatientCommandSnapshotProps {
  patientId: string
}

export default function PatientCommandSnapshot({
  patientId,
}: PatientCommandSnapshotProps) {
  const { data: overview, isLoading } = useOperationsOverview()

  const snapshot = useMemo(() => {
    if (!overview) {
      return null
    }

    const assignedBed = overview.bed_heatmap.find(
      (bed) => bed.patient?.patient_id === patientId
    )
    const queuedPatient = overview.triage_queue.find(
      (entry) => entry.patient_id === patientId
    )
    const patientEvents = overview.timeline.filter((event) => event.patient_id === patientId)

    return {
      assignedBed,
      queuedPatient,
      patientEvents,
      simulation: overview.simulation,
    }
  }, [overview, patientId])

  if (isLoading) {
    return (
      <section className="card">
        <p className="section-label">Command snapshot</p>
        <p className="mt-3 text-sm text-lazarus-muted">
          Loading current routing and scenario state...
        </p>
      </section>
    )
  }

  return (
    <section className="card space-y-5">
      <div>
        <p className="section-label">Command snapshot</p>
        <h2 className="mt-2 font-display text-[2rem] leading-none tracking-[-0.03em] text-lazarus-text">
          Routing and scenario context
        </h2>
        <p className="mt-3 text-sm leading-6 text-lazarus-muted">
          This view ties the patient record back to the live ICU allocator so the
          drill-down still reflects the command room perspective.
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-[1.35rem] border border-lazarus-border/70 bg-lazarus-surface/75 p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
            Primary concern
          </p>
          <p className="mt-2 text-sm leading-6 text-lazarus-text">
            {snapshot?.assignedBed?.patient?.risk_reasons?.[0] ??
              snapshot?.queuedPatient?.risk_reasons?.[0] ??
              snapshot?.queuedPatient?.queue_reason ??
              'No active ICU escalation driver is attached to this patient right now.'}
          </p>
        </div>
        <div className="rounded-[1.35rem] border border-lazarus-border/70 bg-lazarus-surface/75 p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
            Support posture
          </p>
          <p className="mt-2 text-sm leading-6 text-lazarus-text">
            {snapshot?.assignedBed?.patient
              ? `${snapshot.assignedBed.patient.recommended_unit} allocation with ${
                  snapshot.assignedBed.patient.has_active_alert
                    ? 'alert escalation active'
                    : 'continuous monitoring'
                }.`
              : snapshot?.queuedPatient
                ? `${snapshot.queuedPatient.recommended_unit} demand is waiting for live ICU capacity.`
                : 'Outside the current ICU routing set.'}
          </p>
        </div>
        <div className="rounded-[1.35rem] border border-lazarus-border/70 bg-lazarus-surface/75 p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
            Next likely action
          </p>
          <p className="mt-2 text-sm leading-6 text-lazarus-text">
            {snapshot?.queuedPatient
              ? 'Release ICU capacity or route through surge / step-down support.'
              : snapshot?.assignedBed?.patient?.has_active_alert
                ? 'Escalate bedside review and confirm critical support coverage.'
                : snapshot?.assignedBed
                  ? 'Continue monitored ICU placement and vitals review.'
                  : 'Continue observation until command-room pressure changes.'}
          </p>
        </div>
      </div>

      {snapshot?.assignedBed ? (
        <div className="rounded-[1.5rem] border border-lazarus-info/20 bg-lazarus-info/8 p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-lazarus-muted">
                Assigned bed
              </p>
              <p className="mt-2 text-lg font-semibold text-lazarus-text">
                {snapshot.assignedBed.bed_id} • {snapshot.assignedBed.zone}
              </p>
              <p className="mt-1 text-sm text-lazarus-muted">
                {snapshot.assignedBed.assignment_reason}
              </p>
            </div>
            <span className="rounded-full bg-lazarus-surface/80 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-lazarus-text">
              {snapshot.assignedBed.patient?.risk_label} risk
            </span>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-[1.2rem] bg-lazarus-surface/80 px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                Risk score
              </p>
              <p className="mt-1 font-mono text-xl font-semibold text-lazarus-text">
                {snapshot.assignedBed.patient?.risk_score ?? '--'}
              </p>
            </div>
            <div className="rounded-[1.2rem] bg-lazarus-surface/80 px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                Recommended unit
              </p>
              <p className="mt-1 text-base font-semibold text-lazarus-text">
                {snapshot.assignedBed.patient?.recommended_unit ?? '--'}
              </p>
            </div>
            <div className="rounded-[1.2rem] bg-lazarus-surface/80 px-4 py-3">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                Alert state
              </p>
              <p className="mt-1 text-base font-semibold text-lazarus-text">
                {snapshot.assignedBed.patient?.has_active_alert ? 'Escalated' : 'Monitored'}
              </p>
            </div>
          </div>

          {snapshot.assignedBed.patient?.risk_reasons?.length ? (
            <div className="mt-4">
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                Why this patient is high priority
              </p>
              <div className="mt-2 flex flex-wrap gap-2">
                {snapshot.assignedBed.patient.risk_reasons.map((reason) => (
                  <span
                    key={reason}
                    className="rounded-full border border-lazarus-border/70 bg-lazarus-surface/80 px-2.5 py-1 text-[11px] leading-5 text-lazarus-muted"
                  >
                    {reason}
                  </span>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      ) : snapshot?.queuedPatient ? (
        <div className="rounded-[1.5rem] border border-lazarus-warning/25 bg-lazarus-warning/8 p-4">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-lazarus-muted">
                Queue status
              </p>
              <p className="mt-2 text-lg font-semibold text-lazarus-text">
                Awaiting ICU routing
              </p>
              <p className="mt-1 text-sm text-lazarus-muted">
                {snapshot.queuedPatient.queue_reason}
              </p>
            </div>
            <span className="rounded-full bg-lazarus-surface/80 px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] text-lazarus-text">
              {snapshot.queuedPatient.risk_label}
            </span>
          </div>

          {snapshot.queuedPatient.risk_reasons.length ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {snapshot.queuedPatient.risk_reasons.map((reason) => (
                <span
                  key={reason}
                  className="rounded-full border border-lazarus-border/70 bg-lazarus-surface/80 px-2.5 py-1 text-[11px] leading-5 text-lazarus-muted"
                >
                  {reason}
                </span>
              ))}
            </div>
          ) : null}
        </div>
      ) : (
        <div className="rounded-[1.5rem] border border-lazarus-border/70 bg-lazarus-surface/75 p-4">
          <p className="text-sm font-semibold text-lazarus-text">
            No active ICU routing decision for this patient right now.
          </p>
          <p className="mt-2 text-sm text-lazarus-muted">
            The patient is outside the live ICU routing set or has not yet entered the current scenario pressure zone.
          </p>
        </div>
      )}

      <div className="rounded-[1.5rem] border border-lazarus-border/70 bg-lazarus-surface/75 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-lazarus-muted">
              Active scenario
            </p>
            <p className="mt-2 text-lg font-semibold text-lazarus-text">
              {snapshot?.simulation.crisis_label ?? 'Nominal operations'}
            </p>
            <p className="mt-1 text-sm text-lazarus-muted">
              Speed {(snapshot?.simulation.speed ?? 1).toFixed(1)}x
            </p>
          </div>
          <Link
            to="/"
            className="rounded-full border border-lazarus-border bg-lazarus-surface px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-lazarus-info transition-transform hover:-translate-y-0.5"
          >
            Open command center
          </Link>
        </div>
      </div>

      <div>
        <p className="section-label">Latest related events</p>
        {snapshot && snapshot.patientEvents.length > 0 ? (
          <div className="mt-3 space-y-3">
            {snapshot.patientEvents.slice(0, 3).map((event) => (
              <div
                key={event.id}
                className="rounded-[1.25rem] border border-lazarus-border/70 bg-lazarus-surface/70 p-4"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <p className="text-sm font-semibold text-lazarus-text">{event.title}</p>
                  <span className="text-xs uppercase tracking-[0.18em] text-lazarus-muted">
                    {new Date(event.timestamp).toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </span>
                </div>
                <p className="mt-2 text-sm leading-6 text-lazarus-muted">
                  {event.description}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <p className="mt-3 text-sm text-lazarus-muted">
            No direct command-room events are attached to this patient yet.
          </p>
        )}
      </div>
    </section>
  )
}
