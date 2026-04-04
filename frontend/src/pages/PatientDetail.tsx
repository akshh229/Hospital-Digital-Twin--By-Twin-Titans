import { useParams, Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { usePatient } from '../hooks/usePatients'
import { useVitals } from '../hooks/useVitals'
import { usePrescriptions } from '../hooks/usePrescriptions'
import { usePatientRealtime } from '../hooks/usePatientRealtime'
import PatientAlertPanel from '../components/PatientAlertPanel'
import RealtimeStatusBadge from '../components/RealtimeStatusBadge'
import TelemetrySimulatorPanel from '../components/TelemetrySimulatorPanel'
import VitalsChart from '../components/VitalsChart'
import PharmacyTable from '../components/PharmacyTable'

export default function PatientDetail() {
  const { patientId } = useParams<{ patientId: string }>()
  const { data: patient, isLoading: patientLoading } = usePatient(patientId || '')
  const { data: vitals, isLoading: vitalsLoading } = useVitals(patientId || '', 24, {
    refetchInterval: false,
  })
  const { data: prescriptions, isLoading: rxLoading } = usePrescriptions(patientId || '')
  const { connectionState, lastMessageAt, retryAttempt } = usePatientRealtime(patientId || '')
  const [flashTone, setFlashTone] = useState<'live' | 'critical' | null>(null)
  const hasCriticalBpm =
    patient?.last_bpm != null && (patient.last_bpm < 60 || patient.last_bpm > 100)

  useEffect(() => {
    if (!lastMessageAt) {
      return
    }

    setFlashTone(hasCriticalBpm ? 'critical' : 'live')
    const timeoutId = window.setTimeout(() => setFlashTone(null), 900)
    return () => window.clearTimeout(timeoutId)
  }, [hasCriticalBpm, lastMessageAt])

  if (patientLoading) {
    return <div className="text-lazarus-muted">Loading patient data...</div>
  }

  if (!patient) {
    return (
      <div className="card">
        <h2 className="text-lazarus-critical font-semibold">Patient Not Found</h2>
        <Link to="/" className="text-lazarus-info text-sm mt-2 inline-block">
          Back to Dashboard
        </Link>
      </div>
    )
  }

  return (
    <div className="page-entrance space-y-6">
      <Link
        to="/"
        className="inline-flex items-center gap-2 rounded-full border border-lazarus-border bg-lazarus-surface/92 px-4 py-2 text-sm font-semibold text-lazarus-info transition-transform duration-300 hover:-translate-x-1 hover:bg-lazarus-surface-high"
      >
        &larr; Back to Dashboard
      </Link>

      <div
        className={`hero-panel ${
          flashTone === 'critical'
            ? 'critical-shell-flash'
            : flashTone === 'live'
              ? 'live-shell-flash'
              : ''
        } ${hasCriticalBpm ? 'hero-panel-critical animate-pulse-critical-subtle' : ''}`}
      >
        <div className="relative z-10 flex flex-col gap-8 xl:flex-row xl:items-end xl:justify-between">
          <div className="min-w-0 flex-1 max-w-3xl">
            <p className="display-kicker">Case dossier</p>
            <div className="mt-3 flex flex-wrap items-center gap-3">
              <h1 className="font-display text-[2.6rem] leading-none tracking-[-0.04em] text-lazarus-text sm:text-[3.4rem]">
                {patient.name || `Patient ${patient.patient_raw_id}`}
              </h1>
              {patient.has_active_alert && <span className="badge-critical">Critical</span>}
              <RealtimeStatusBadge
                state={connectionState}
                retryAttempt={retryAttempt}
                liveLabel="Live monitor"
                connectingLabel="Connecting monitor"
                reconnectingLabel="Reconnecting monitor"
                offlineLabel="Monitor offline"
              />
            </div>
            <p className="mt-5 max-w-2xl text-base leading-7 text-lazarus-muted">
              Continuous telemetry, reconciled identity mapping, and decrypted medication
              history in a single patient recovery workspace.
            </p>
            <div className="mt-7 flex flex-wrap gap-2">
              <span className="dossier-chip">Age {patient.age}</span>
              <span className="dossier-chip">Ward {patient.ward}</span>
              <span className="dossier-chip">Raw ID {patient.patient_raw_id}</span>
              <span className="dossier-chip">Parity {patient.parity_flag}</span>
              <span className="dossier-chip">
                Confidence{' '}
                {patient.identity_confidence
                  ? `${(patient.identity_confidence * 100).toFixed(0)}%`
                  : 'N/A'}
              </span>
              {lastMessageAt && (
                <span className="dossier-chip">
                  Last signal{' '}
                  {new Date(lastMessageAt).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit',
                  })}
                </span>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 xl:min-w-[22rem]">
            <div
              className={`metric-frame text-center transition-all duration-500 ${
                flashTone === 'critical'
                  ? 'critical-vitals-card'
                  : flashTone === 'live'
                    ? 'live-vitals-card'
                    : ''
              }`}
            >
              <p className="vitals-label">Heart rate</p>
              <p
                className={`vitals-value ${
                  patient.last_bpm && (patient.last_bpm < 60 || patient.last_bpm > 100)
                    ? 'text-lazarus-critical'
                    : 'text-lazarus-normal'
                }`}
              >
                {patient.last_bpm ?? '--'}
              </p>
            </div>
            <div
              className={`metric-frame text-center transition-all duration-500 delay-75 ${
                flashTone === 'critical'
                  ? 'critical-vitals-card'
                  : flashTone === 'live'
                    ? 'live-vitals-card'
                    : ''
              }`}
            >
              <p className="vitals-label">Oxygen</p>
              <p
                className={`vitals-value ${
                  patient.last_oxygen && patient.last_oxygen < 90
                    ? 'text-lazarus-critical'
                    : 'text-lazarus-normal'
                }`}
              >
                {patient.last_oxygen != null ? `${patient.last_oxygen}%` : '--'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {patientId && <PatientAlertPanel patientId={patientId} />}
      {patientId && (
        <TelemetrySimulatorPanel
          patientId={patientId}
          connectionState={connectionState}
        />
      )}

      <div className="mb-6">
        {vitalsLoading ? (
          <div className="card text-lazarus-muted">Loading vitals...</div>
        ) : vitals && vitals.data.length > 0 ? (
          <div
            className={
              flashTone === 'critical'
                ? 'critical-shell-flash rounded-xl'
                : flashTone === 'live'
                  ? 'live-shell-flash rounded-xl'
                  : ''
            }
          >
            <VitalsChart data={vitals.data} title="Vitals integrity monitor" />
          </div>
        ) : (
          <div className="card text-lazarus-muted">No vitals data available for this patient.</div>
        )}
      </div>

      {rxLoading ? (
        <div className="card text-lazarus-muted">Loading prescriptions...</div>
      ) : (
        <PharmacyTable prescriptions={prescriptions || []} />
      )}
    </div>
  )
}
