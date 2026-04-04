import {
  AlertOctagon,
  BellOff,
  CheckCircle2,
  Clock3,
  ShieldCheck,
} from 'lucide-react'
import { useAcknowledgeAlert, useAlertHistory, useAlerts } from '../hooks/useAlerts'

interface PatientAlertPanelProps {
  patientId: string
}

function formatDateTime(value: string) {
  return new Date(value).toLocaleString([], {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function formatStatus(status: string) {
  return status.charAt(0).toUpperCase() + status.slice(1)
}

export default function PatientAlertPanel({ patientId }: PatientAlertPanelProps) {
  const { data: alerts, isLoading: alertsLoading } = useAlerts()
  const { data: history, isLoading: historyLoading } = useAlertHistory(patientId)
  const acknowledgeAlert = useAcknowledgeAlert()

  const activeAlert = alerts?.find((alert) => alert.patient_id === patientId)

  return (
    <div className="mb-6 grid gap-4 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
      <section className={`card ${activeAlert ? 'card-critical' : ''}`}>
        <div className="mb-4 flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-sm font-semibold uppercase tracking-wide text-lazarus-text">
              Active Alert
            </h2>
            <p className="mt-1 text-sm text-lazarus-muted">
              Clinician acknowledgement and current alert state.
            </p>
          </div>
          {activeAlert ? (
            <span className="badge-critical">
              <AlertOctagon size={14} strokeWidth={2.5} /> Open
            </span>
          ) : (
            <span className="badge-normal">
              <CheckCircle2 size={14} strokeWidth={2.5} /> Clear
            </span>
          )}
        </div>

        {alertsLoading ? (
          <p className="text-sm text-lazarus-muted">Checking current alert state...</p>
        ) : activeAlert ? (
          <div className="space-y-4">
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-xl bg-lazarus-surface-low/80 p-4 ring-1 ring-lazarus-border/25">
                <p className="vitals-label">Opened</p>
                <p className="mt-2 text-sm font-medium text-lazarus-text">
                  {formatDateTime(activeAlert.opened_at)}
                </p>
              </div>
              <div className="rounded-xl bg-lazarus-surface-low/80 p-4 ring-1 ring-lazarus-border/25">
                <p className="vitals-label">Last BPM</p>
                <p className="mt-2 text-2xl font-mono font-bold text-lazarus-critical">
                  {activeAlert.last_bpm ?? '--'}
                </p>
              </div>
              <div className="rounded-xl bg-lazarus-surface-low/80 p-4 ring-1 ring-lazarus-border/25">
                <p className="vitals-label">Abnormal Count</p>
                <p className="mt-2 text-2xl font-mono font-bold text-lazarus-text">
                  {activeAlert.consecutive_abnormal_count}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl bg-lazarus-surface/94 p-4 ring-1 ring-lazarus-border/70">
              <div className="flex items-start gap-3">
                <ShieldCheck className="mt-0.5 text-lazarus-warning" size={18} />
                <div>
                  <p className="text-sm font-semibold text-lazarus-text">
                    Alert acknowledgement available
                  </p>
                  <p className="text-sm text-lazarus-muted">
                    Mark this alert as reviewed to clear it from the active queue.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() =>
                  acknowledgeAlert.mutate({ alertId: activeAlert.id, patientId })
                }
                disabled={acknowledgeAlert.isPending}
                className="inline-flex items-center gap-2 rounded-lg bg-lazarus-accent px-4 py-2 text-sm font-semibold text-white transition-transform duration-200 hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <BellOff size={15} />
                {acknowledgeAlert.isPending ? 'Acknowledging...' : 'Acknowledge Alert'}
              </button>
            </div>
          </div>
        ) : (
          <div className="rounded-xl bg-lazarus-surface-low/80 p-5 ring-1 ring-lazarus-border/25">
            <p className="text-sm font-semibold text-lazarus-text">
              No active critical alert for this patient.
            </p>
            <p className="mt-2 text-sm text-lazarus-muted">
              The realtime monitor is still active and will surface a new alert here if the
              patient crosses the abnormal threshold.
            </p>
          </div>
        )}
      </section>

      <section className="card">
        <div className="mb-4">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-lazarus-text">
            Alert Timeline
          </h2>
          <p className="mt-1 text-sm text-lazarus-muted">
            Recent closed alerts for quick forensic review.
          </p>
        </div>

        {historyLoading ? (
          <p className="text-sm text-lazarus-muted">Loading alert history...</p>
        ) : history && history.length > 0 ? (
          <div className="space-y-3">
            {history.slice(0, 6).map((entry) => (
              <div
                key={entry.id}
                className="rounded-xl bg-lazarus-surface-low/80 p-4 ring-1 ring-lazarus-border/25"
              >
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-lazarus-text">
                      Alert #{entry.id}
                    </p>
                    <p className="mt-1 text-xs text-lazarus-muted">
                      Opened {formatDateTime(entry.opened_at)}
                    </p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="inline-flex items-center gap-1.5 rounded-full bg-lazarus-surface/94 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-lazarus-muted ring-1 ring-lazarus-border/70">
                      <Clock3 size={12} />
                      {entry.duration_minutes != null
                        ? `${entry.duration_minutes} min`
                        : 'Pending'}
                    </span>
                    <span className="inline-flex items-center rounded-full bg-lazarus-surface/94 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-lazarus-text ring-1 ring-lazarus-border/70">
                      {formatStatus(entry.status)}
                    </span>
                  </div>
                </div>
                <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="vitals-label">Last BPM</p>
                    <p className="mt-1 font-mono text-lazarus-text">{entry.last_bpm}</p>
                  </div>
                  <div>
                    <p className="vitals-label">Last SpO2</p>
                    <p className="mt-1 font-mono text-lazarus-text">{entry.last_oxygen}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="rounded-xl bg-lazarus-surface-low/80 p-5 ring-1 ring-lazarus-border/25">
            <p className="text-sm font-semibold text-lazarus-text">No closed alerts yet.</p>
            <p className="mt-2 text-sm text-lazarus-muted">
              Once this patient has a completed alert cycle, the timeline will show it here.
            </p>
          </div>
        )}
      </section>
    </div>
  )
}
