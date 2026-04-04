import { usePatients } from '../hooks/usePatients'
import PatientCard from '../components/PatientCard'

export default function Dashboard() {
  const { data: patients, isLoading, error } = usePatients()

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-lazarus-muted">Loading patients...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card border-lazarus-critical">
        <h2 className="text-lazarus-critical font-semibold mb-2">Connection Error</h2>
        <p className="text-lazarus-muted text-sm">
          Unable to connect to the Lazarus backend. Ensure the server is running at http://localhost:8000
        </p>
      </div>
    )
  }

  if (!patients || patients.length === 0) {
    return (
      <div className="card">
        <h2 className="text-lazarus-text font-semibold mb-2">No Patient Data</h2>
        <p className="text-lazarus-muted text-sm">
          No patients found. Run the seed data generator to populate the system:
        </p>
        <code className="block mt-2 text-xs text-lazarus-info font-mono">
          python seed_data/generate_seeds.py && python seed_data/load_seeds.py
        </code>
      </div>
    )
  }

  const criticalPatients = patients.filter((p) => p.has_active_alert)
  const stablePatients = patients.filter((p) => !p.has_active_alert)
  const averageBpm = Math.round(
    patients.reduce((sum, patient) => sum + (patient.last_bpm ?? 0), 0) /
      Math.max(patients.filter((patient) => patient.last_bpm != null).length, 1)
  )
  const averageOxygen = Math.round(
    patients.reduce((sum, patient) => sum + (patient.last_oxygen ?? 0), 0) /
      Math.max(patients.filter((patient) => patient.last_oxygen != null).length, 1)
  )

  return (
    <div className="page-entrance space-y-10">
      <section className="hero-panel">
        <div className="relative z-10 grid gap-8 xl:grid-cols-[minmax(0,1.25fr)_minmax(18rem,0.75fr)] xl:items-end">
          <div className="max-w-3xl">
            <p className="display-kicker">Live census</p>
            <h1 className="display-title mt-3">Recovered telemetry across the active clinical census.</h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-lazarus-muted">
              Lazarus tracks recovered patient records, reconciles identity collisions,
              and surfaces unstable telemetry with a calmer, more premium clinical
              presentation.
            </p>
            <div className="mt-7 flex flex-wrap gap-2">
              <span className="dossier-chip">Recovered records {patients.length}</span>
              <span className="dossier-chip">Critical watch {criticalPatients.length}</span>
              <span className="dossier-chip">Stable census {stablePatients.length}</span>
            </div>
          </div>

          <div className="shell-frame space-y-4">
            <div className="flex items-end justify-between gap-4">
              <div>
                <p className="section-label">Clinical pulse</p>
                <p className="mt-2 font-display text-[2.35rem] leading-none tracking-[-0.04em] text-lazarus-text">
                  {averageBpm}
                </p>
                <p className="mt-2 text-sm text-lazarus-muted">Average heart rate across live patients</p>
              </div>
              <div className="text-right">
                <p className="section-label">Oxygen baseline</p>
                <p className="mt-2 font-mono text-[2rem] font-semibold tracking-[-0.05em] text-lazarus-info">
                  {averageOxygen}%
                </p>
              </div>
            </div>
            <div className="dossier-divider" />
            <div className="grid grid-cols-3 gap-3">
              <div className="metric-frame">
                <p className="section-label">Total</p>
                <p className="metric-value">{patients.length}</p>
              </div>
              <div className="metric-frame">
                <p className="section-label text-lazarus-critical/80">Critical</p>
                <p className="metric-value text-lazarus-critical">{criticalPatients.length}</p>
              </div>
              <div className="metric-frame">
                <p className="section-label text-lazarus-normal/80">Stable</p>
                <p className="metric-value text-lazarus-normal">{stablePatients.length}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {criticalPatients.length > 0 && (
        <section className="space-y-4">
          <div className="flex flex-wrap items-end justify-between gap-3">
            <div>
              <p className="section-label text-lazarus-critical/85">Immediate attention</p>
              <h2 className="mt-2 font-display text-[2rem] leading-none tracking-[-0.03em] text-lazarus-text">
                Critical patients
              </h2>
            </div>
            <p className="text-sm text-lazarus-muted">
              {criticalPatients.length} records currently breaching the safe telemetry band.
            </p>
          </div>
          <div className="dossier-divider" />
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
            {criticalPatients.map((patient, index) => (
              <PatientCard key={patient.patient_id} patient={patient} index={index} />
            ))}
          </div>
        </section>
      )}

      <section className="space-y-4">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="section-label">Recovered census</p>
            <h2 className="mt-2 font-display text-[2rem] leading-none tracking-[-0.03em] text-lazarus-text">
              Stable patients
            </h2>
          </div>
          <p className="text-sm text-lazarus-muted">
            {stablePatients.length} active records are inside safe monitoring thresholds.
          </p>
        </div>
        <div className="dossier-divider" />
        <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
          {stablePatients.map((patient, index) => (
            <PatientCard
              key={patient.patient_id}
              patient={patient}
              index={criticalPatients.length + index}
            />
          ))}
        </div>
      </section>
    </div>
  )
}
