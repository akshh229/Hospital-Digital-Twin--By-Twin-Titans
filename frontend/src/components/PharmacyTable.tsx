import type { Prescription } from '../types'

interface PharmacyTableProps {
  prescriptions: Prescription[]
}

export default function PharmacyTable({ prescriptions }: PharmacyTableProps) {
  if (!prescriptions || prescriptions.length === 0) {
    return (
      <div className="card">
        <h3 className="text-sm font-semibold text-lazarus-text mb-4">Pharmacy Portal</h3>
        <p className="text-lazarus-muted text-sm">No prescriptions found.</p>
      </div>
    )
  }

  return (
    <div className="card">
      <div className="mb-5">
        <p className="section-label">Medication ledger</p>
        <h3 className="mt-2 font-display text-[2rem] leading-none tracking-[-0.03em] text-lazarus-text">
          Pharmacy decryption log
        </h3>
      </div>
      <div className="space-y-3 md:hidden">
        {prescriptions.map((rx) => (
          <div
            key={rx.id}
            className="rounded-[1.35rem] border border-lazarus-border bg-lazarus-surface/94 p-4 ring-1 ring-lazarus-border/35"
          >
            <div className="mb-3 flex items-center justify-between gap-3">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-lazarus-muted">
                  Timestamp
                </p>
                <p className="font-mono text-xs text-lazarus-text">
                  {new Date(rx.timestamp).toLocaleString([], {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
              <span className="dossier-chip">RX record</span>
            </div>
            <div className="space-y-3 text-sm">
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-lazarus-muted">
                  Encrypted
                </p>
                <p className="font-mono text-xs text-lazarus-warning/80 break-all">
                  {rx.med_cipher_text}
                </p>
              </div>
              <div>
                <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-lazarus-muted">
                  Decrypted
                </p>
                <p className="font-mono font-semibold text-lazarus-normal">
                  {rx.med_decoded_name || '???'}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-lazarus-muted">
                    Dose
                  </p>
                  <p>{rx.dosage || '--'}</p>
                </div>
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.08em] text-lazarus-muted">
                    Route
                  </p>
                  <p>{rx.route || '--'}</p>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="hidden overflow-x-auto md:block">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-lazarus-border text-left text-lazarus-muted">
              <th className="pb-3 pr-4 font-semibold tracking-wider uppercase text-xs">Time</th>
              <th className="pb-3 pr-4 font-semibold tracking-wider uppercase text-xs">Encrypted</th>
              <th className="pb-3 pr-4 font-semibold tracking-wider uppercase text-xs">Decrypted</th>
              <th className="pb-3 pr-4 font-semibold tracking-wider uppercase text-xs">Dose</th>
              <th className="pb-3 font-semibold tracking-wider uppercase text-xs">Route</th>
            </tr>
          </thead>
          <tbody>
            {prescriptions.map((rx) => (
              <tr key={rx.id} className="border-b border-lazarus-border/70 transition-colors hover:bg-lazarus-surface-high/80">
                <td className="py-3 pr-4 font-mono text-xs text-lazarus-muted">
                  {new Date(rx.timestamp).toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
                </td>
                <td className="py-3 pr-4 font-mono text-lazarus-warning/80 tracking-wide text-xs">
                  {rx.med_cipher_text}
                </td>
                <td className="py-2 pr-4 font-mono text-lazarus-normal font-semibold">
                  {rx.med_decoded_name || '???'}
                </td>
                <td className="py-2 pr-4">
                  {rx.dosage || '--'}
                </td>
                <td className="py-2">
                  {rx.route || '--'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
