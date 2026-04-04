import { Link } from 'react-router-dom'
import { CheckCircle2, AlertTriangle, AlertOctagon } from 'lucide-react'
import type { Patient } from '../types'

interface PatientCardProps {
  patient: Patient
  isSelected?: boolean
  index?: number
}

export default function PatientCard({ patient, isSelected, index = 0 }: PatientCardProps) {
  const bpmStatus = patient.last_bpm
    ? patient.last_bpm >= 60 && patient.last_bpm <= 100
      ? 'normal'
      : 'critical'
    : 'unknown'

  return (
    <Link to={`/patient/${patient.patient_id}`} className="block">
      <div
        className={`card patient-card group card-entrance card-interactive cursor-pointer ${
          patient.has_active_alert
            ? 'card-critical patient-card-critical animate-pulse-critical-subtle'
            : ''
        } ${
          isSelected
            ? 'ring-lazarus-accent/50 bg-lazarus-surface-high/60'
            : 'hover:bg-lazarus-surface-high'
        }`}
        style={{ animationDelay: `${Math.min(index, 8) * 70}ms` }}
      >
        <div className="mb-8 flex items-start justify-between gap-6">
          <div className="min-w-0 pr-4">
            <p className="section-label">
              Case file {patient.patient_raw_id}
            </p>
            <h3 className="mt-3 text-[2rem] font-semibold leading-[1.02] tracking-[-0.05em] text-lazarus-text sm:text-[2.2rem]">
              {patient.name || `Patient ${patient.patient_raw_id}`}
            </h3>
            <p className="mt-3 max-w-sm text-sm font-medium text-lazarus-muted">
              Age {patient.age || 'N/A'} <span className="mx-2 opacity-35">•</span>
              Ward {patient.ward || 'N/A'}
            </p>
          </div>
          <div className="shrink-0">
            {bpmStatus === 'normal' && (
              <span className="badge-normal">
                <CheckCircle2 size={14} strokeWidth={2.5} /> Stable
              </span>
            )}
            {bpmStatus === 'critical' && (
              <span className="badge-critical">
                <AlertOctagon size={14} strokeWidth={2.5} /> Critical
              </span>
            )}
            {bpmStatus === 'unknown' && (
              <span className="badge-warning">
                <AlertTriangle size={14} strokeWidth={2.5} /> No Data
              </span>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div className="flex flex-col gap-2 transition-transform duration-300 group-hover:-translate-y-0.5">
            <p className="vitals-label">Heart rate</p>
            <p className={`vitals-value ${bpmStatus === 'critical' ? 'text-lazarus-critical' : 'text-lazarus-text'}`}>
              {patient.last_bpm ?? '--'}
            </p>
          </div>
          <div className="flex flex-col gap-2 transition-transform duration-300 delay-75 group-hover:-translate-y-0.5">
            <p className="vitals-label">Oxygen saturation</p>
            <p className={`vitals-value ${patient.last_oxygen && patient.last_oxygen < 90 ? 'text-lazarus-critical' : 'text-lazarus-text'}`}>
              {patient.last_oxygen != null ? `${patient.last_oxygen}%` : '--'}
            </p>
          </div>
        </div>

        <div className="mt-8">
          <div className="dossier-divider" />
          <div className="mt-5 flex flex-wrap items-center gap-2">
            <span className="dossier-chip">Parity {patient.parity_flag}</span>
            <span className="dossier-chip">Prescriptions {patient.prescription_count}</span>
            <span className="dossier-chip">Monitor ready</span>
          </div>
        </div>
      </div>
    </Link>
  )
}
