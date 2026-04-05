import type {
  BedAvailabilityFilter,
  BedTile,
  TriageQueueEntry,
} from '../types'

interface RoomAvailabilityPanelProps {
  beds: BedTile[]
  triageQueue: TriageQueueEntry[]
  availabilityFilter: BedAvailabilityFilter
  selectedZone: string | null
  onAvailabilityFilterChange: (filter: BedAvailabilityFilter) => void
  onZoneChange: (zone: string | null) => void
}

interface ZoneAvailabilitySummary {
  zone: string
  total: number
  available: number
  occupied: number
}

const availabilityLabels: Record<BedAvailabilityFilter, string> = {
  all: 'All beds',
  available: 'Available now',
  occupied: 'Occupied only',
}

function filterButtonClass(isActive: boolean) {
  if (isActive) {
    return 'border-lazarus-info bg-lazarus-info/12 text-lazarus-info'
  }

  return 'border-lazarus-border bg-lazarus-surface text-lazarus-text'
}

export default function RoomAvailabilityPanel({
  beds,
  triageQueue,
  availabilityFilter,
  selectedZone,
  onAvailabilityFilterChange,
  onZoneChange,
}: RoomAvailabilityPanelProps) {
  const occupiedBeds = beds.filter((bed) => bed.status === 'occupied').length
  const availableBeds = beds.filter((bed) => bed.status === 'available')
  const openZones = new Set(availableBeds.map((bed) => bed.zone)).size

  const zoneSummaries = beds.reduce<ZoneAvailabilitySummary[]>((accumulator, bed) => {
    const existing = accumulator.find((entry) => entry.zone === bed.zone)
    if (existing) {
      existing.total += 1
      if (bed.status === 'available') {
        existing.available += 1
      } else {
        existing.occupied += 1
      }
      return accumulator
    }

    accumulator.push({
      zone: bed.zone,
      total: 1,
      available: bed.status === 'available' ? 1 : 0,
      occupied: bed.status === 'occupied' ? 1 : 0,
    })
    return accumulator
  }, [])

  const visibleAvailableBeds = availableBeds.filter((bed) => {
    if (!selectedZone) {
      return true
    }

    return bed.zone === selectedZone
  })

  const selectedZoneLabel = selectedZone ?? 'All zones'

  return (
    <section className="card space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="section-label">Room availability</p>
          <h2 className="mt-2 font-display text-[2rem] font-semibold leading-none tracking-[-0.03em] text-lazarus-text">
            Open bed command view
          </h2>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-lazarus-muted">
            Scan immediate ICU headroom, see which zones still have routing space, and
            filter the live ward map before you reassign patients.
          </p>
        </div>
        <span
          className={`rounded-full px-3 py-1.5 text-xs font-semibold uppercase tracking-[0.16em] ${
            availableBeds.length > 0
              ? 'bg-lazarus-normal/12 text-lazarus-normal'
              : 'bg-lazarus-critical/10 text-lazarus-critical'
          }`}
        >
          {availableBeds.length > 0
            ? `${availableBeds.length} ready now`
            : 'No open rooms'}
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        <article className="subcard">
          <p className="section-label">Ready now</p>
          <p className="mt-2 font-mono text-[1.8rem] font-semibold tracking-[-0.04em] text-lazarus-normal">
            {availableBeds.length}
          </p>
        </article>
        <article className="subcard">
          <p className="section-label">Occupied</p>
          <p className="mt-2 font-mono text-[1.8rem] font-semibold tracking-[-0.04em] text-lazarus-text">
            {occupiedBeds}
          </p>
        </article>
        <article className="subcard">
          <p className="section-label">Overflow waiting</p>
          <p className="mt-2 font-mono text-[1.8rem] font-semibold tracking-[-0.04em] text-lazarus-critical">
            {triageQueue.length}
          </p>
        </article>
        <article className="subcard">
          <p className="section-label">Zones open</p>
          <p className="mt-2 font-mono text-[1.8rem] font-semibold tracking-[-0.04em] text-lazarus-info">
            {openZones}
          </p>
        </article>
      </div>

      <div className="shell-frame space-y-4">
        <div>
          <p className="section-label">Map filter</p>
          <div className="mt-3 flex flex-wrap gap-2">
            {Object.entries(availabilityLabels).map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={`rounded-full border px-3 py-2 text-sm font-semibold transition-transform hover:-translate-y-0.5 ${filterButtonClass(
                  availabilityFilter === value
                )}`}
                aria-pressed={availabilityFilter === value}
                onClick={() => onAvailabilityFilterChange(value as BedAvailabilityFilter)}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="section-label">Zone focus</p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              className={`rounded-full border px-3 py-2 text-sm font-semibold transition-transform hover:-translate-y-0.5 ${filterButtonClass(
                selectedZone === null
              )}`}
              aria-pressed={selectedZone === null}
              onClick={() => onZoneChange(null)}
            >
              All zones
            </button>
            {zoneSummaries.map((summary) => (
              <button
                key={summary.zone}
                type="button"
                className={`rounded-full border px-3 py-2 text-sm font-semibold transition-transform hover:-translate-y-0.5 ${filterButtonClass(
                  selectedZone === summary.zone
                )}`}
                aria-pressed={selectedZone === summary.zone}
                onClick={() => onZoneChange(summary.zone)}
              >
                {summary.zone} {summary.available} ready
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
        <article className="subcard">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="section-label">Available bed IDs</p>
              <p className="mt-1 text-sm text-lazarus-muted">{selectedZoneLabel}</p>
            </div>
            <span className="dossier-chip">{visibleAvailableBeds.length} open</span>
          </div>

          {visibleAvailableBeds.length > 0 ? (
            <div className="mt-4 flex flex-wrap gap-2">
              {visibleAvailableBeds.map((bed) => (
                <span key={bed.bed_id} className="badge-normal">
                  {bed.bed_id}
                </span>
              ))}
            </div>
          ) : (
            <p className="mt-4 text-sm leading-6 text-lazarus-muted">
              No open ICU beds match the current zone selection.
            </p>
          )}
        </article>

        <article className="subcard">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="section-label">Zone balance</p>
              <p className="mt-1 text-sm text-lazarus-muted">
                Live routing headroom by pod
              </p>
            </div>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            {zoneSummaries.map((summary) => (
              <div
                key={summary.zone}
                className="rounded-[1.2rem] border border-lazarus-border/70 bg-lazarus-surface/76 px-4 py-3"
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="text-sm font-semibold text-lazarus-text">{summary.zone}</p>
                  <span
                    className={`rounded-full px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.14em] ${
                      summary.available > 0
                        ? 'bg-lazarus-normal/12 text-lazarus-normal'
                        : 'bg-lazarus-warning/12 text-lazarus-warning'
                    }`}
                  >
                    {summary.available > 0 ? 'Open' : 'Full'}
                  </span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2 text-xs text-lazarus-muted">
                  <span className="dossier-chip">Ready {summary.available}</span>
                  <span className="dossier-chip">Occupied {summary.occupied}</span>
                  <span className="dossier-chip">Total {summary.total}</span>
                </div>
              </div>
            ))}
          </div>
        </article>
      </div>
    </section>
  )
}
