import { Link } from 'react-router-dom'
import type { BedTile, TriageQueueEntry } from '../types'

interface ICUBedHeatmapProps {
  beds: BedTile[]
  triageQueue: TriageQueueEntry[]
}

function toneForBed(tile: BedTile) {
  if (tile.status === 'available') {
    return 'border-lazarus-normal/25 bg-lazarus-normal/8'
  }

  const riskLabel = tile.patient?.risk_label ?? 'Stable'
  if (riskLabel === 'Critical') {
    return 'border-lazarus-critical/35 bg-lazarus-critical/10'
  }
  if (riskLabel === 'High') {
    return 'border-lazarus-warning/35 bg-lazarus-warning/10'
  }
  if (riskLabel === 'Guarded') {
    return 'border-lazarus-info/35 bg-lazarus-info/10'
  }
  return 'border-lazarus-normal/30 bg-lazarus-normal/10'
}

function toneForQueue(entry: TriageQueueEntry) {
  if (entry.risk_label === 'Critical') {
    return 'border-lazarus-critical/30 bg-lazarus-critical/8'
  }
  if (entry.risk_label === 'High') {
    return 'border-lazarus-warning/30 bg-lazarus-warning/8'
  }
  return 'border-lazarus-info/25 bg-lazarus-info/8'
}

function RiskReasonTags({ reasons }: { reasons: string[] }) {
  if (reasons.length === 0) {
    return null
  }

  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
        Why flagged
      </p>
      <div className="mt-2 flex flex-wrap gap-2">
        {reasons.slice(0, 2).map((reason) => (
          <span
            key={reason}
            className="rounded-full border border-lazarus-border/70 bg-lazarus-surface/85 px-2.5 py-1 text-[11px] leading-5 text-lazarus-muted"
          >
            {reason}
          </span>
        ))}
      </div>
    </div>
  )
}

export default function ICUBedHeatmap({
  beds,
  triageQueue,
}: ICUBedHeatmapProps) {
  const occupiedBeds = beds.filter((bed) => bed.status === 'occupied').length

  return (
    <section className="card space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="section-label">Live ICU bed heatmap</p>
          <h2 className="mt-2 font-display text-[2rem] font-semibold leading-none tracking-[-0.03em] text-lazarus-text">
            Ward allocation map
          </h2>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="dossier-chip">Occupied {occupiedBeds}</span>
          <span className="dossier-chip">Available {beds.length - occupiedBeds}</span>
          <span className="dossier-chip">Overflow {triageQueue.length}</span>
        </div>
      </div>

      <p className="text-sm leading-6 text-lazarus-muted">
        Beds are routed by live risk score, alert state, and current ICU pressure.
        Click an occupied bed to drill into the patient timeline.
      </p>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {beds.map((tile) => {
          const content = (
            <div
              className={`rounded-[1.4rem] border p-4 transition-transform duration-300 hover:-translate-y-0.5 ${toneForBed(tile)}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.24em] text-lazarus-muted">
                    {tile.zone}
                  </p>
                  <h3 className="mt-2 font-mono text-lg font-semibold text-lazarus-text">
                    {tile.bed_id}
                  </h3>
                </div>
                <span
                  className={`rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] ${
                    tile.status === 'occupied'
                      ? 'bg-lazarus-surface text-lazarus-text'
                      : 'bg-lazarus-normal/12 text-lazarus-normal'
                  }`}
                >
                  {tile.status === 'occupied' ? tile.patient?.risk_label : 'Ready'}
                </span>
              </div>

              {tile.patient ? (
                <div className="mt-4 space-y-3">
                  <div>
                    <p className="text-sm font-semibold text-lazarus-text">
                      {tile.patient.patient_name || `Patient ${tile.patient.patient_raw_id}`}
                    </p>
                    <p className="mt-1 text-xs leading-5 text-lazarus-muted">
                      {tile.assignment_reason}
                    </p>
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    <div className="rounded-2xl bg-lazarus-surface/80 px-3 py-2">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                        Risk
                      </p>
                      <p className="mt-1 font-mono text-base font-semibold text-lazarus-text">
                        {tile.patient.risk_score}
                      </p>
                    </div>
                    <div className="rounded-2xl bg-lazarus-surface/80 px-3 py-2">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                        BPM
                      </p>
                      <p className="mt-1 font-mono text-base font-semibold text-lazarus-text">
                        {tile.patient.last_bpm ?? '--'}
                      </p>
                    </div>
                    <div className="rounded-2xl bg-lazarus-surface/80 px-3 py-2">
                      <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                        SpO2
                      </p>
                      <p className="mt-1 font-mono text-base font-semibold text-lazarus-text">
                        {tile.patient.last_oxygen != null ? `${tile.patient.last_oxygen}%` : '--'}
                      </p>
                    </div>
                  </div>

                  <RiskReasonTags reasons={tile.patient.risk_reasons} />
                </div>
              ) : (
                <div className="mt-4 rounded-[1.25rem] border border-dashed border-lazarus-normal/30 bg-lazarus-surface/70 px-4 py-6">
                  <p className="text-sm font-semibold text-lazarus-normal">Bed standing by</p>
                  <p className="mt-2 text-xs leading-5 text-lazarus-muted">
                    {tile.assignment_reason}
                  </p>
                </div>
              )}
            </div>
          )

          if (!tile.patient) {
            return <div key={tile.bed_id}>{content}</div>
          }

          return (
            <Link key={tile.bed_id} to={`/patient/${tile.patient.patient_id}`} className="block">
              {content}
            </Link>
          )
        })}
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="section-label">Triage queue</p>
            <p className="mt-1 text-sm text-lazarus-muted">
              Patients awaiting routing because live ICU capacity is fully engaged.
            </p>
          </div>
        </div>

        {triageQueue.length > 0 ? (
          <div className="grid gap-3 md:grid-cols-2">
            {triageQueue.map((entry) => (
              <Link
                key={entry.patient_id}
                to={`/patient/${entry.patient_id}`}
                className={`rounded-[1.35rem] border p-4 transition-transform duration-300 hover:-translate-y-0.5 ${toneForQueue(entry)}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-lazarus-text">
                      {entry.patient_name || `Patient ${entry.patient_raw_id}`}
                    </p>
                    <p className="mt-1 text-xs leading-5 text-lazarus-muted">
                      {entry.queue_reason}
                    </p>
                    <div className="mt-3">
                      <RiskReasonTags reasons={entry.risk_reasons} />
                    </div>
                  </div>
                  <span className="rounded-full bg-lazarus-surface/80 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-lazarus-text">
                    {entry.risk_label}
                  </span>
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="rounded-[1.35rem] border border-lazarus-border/70 bg-lazarus-surface/70 px-4 py-5 text-sm text-lazarus-muted">
            No overflow queue right now. All current critical demand fits inside the live ICU map.
          </div>
        )}
      </div>
    </section>
  )
}
