import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ResourceCard, ResourceForecastPoint } from '../types'

interface ResourceConsumptionPanelProps {
  cards: ResourceCard[]
  forecast: ResourceForecastPoint[]
}

function toneForStatus(status: ResourceCard['status']) {
  if (status === 'critical') {
    return 'border-lazarus-critical/35 bg-lazarus-critical/10'
  }
  if (status === 'warning') {
    return 'border-lazarus-warning/35 bg-lazarus-warning/10'
  }
  return 'border-lazarus-normal/30 bg-lazarus-normal/10'
}

function formatResourceValue(card: ResourceCard) {
  if (card.unit === '%') {
    return `${card.available}%`
  }

  return `${card.available}/${card.capacity}`
}

export default function ResourceConsumptionPanel({
  cards,
  forecast,
}: ResourceConsumptionPanelProps) {
  return (
    <section className="card space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="section-label">Predictive resource consumption</p>
          <h2 className="mt-2 font-display text-[2rem] font-semibold leading-none tracking-[-0.03em] text-lazarus-text">
            Burn-rate forecast
          </h2>
        </div>
        <span className="dossier-chip">6-step projection window</span>
      </div>

      <div className="grid gap-3 md:grid-cols-2">
        {cards.map((card) => (
          <div
            key={card.resource_key}
            className={`rounded-[1.35rem] border p-4 ${toneForStatus(card.status)}`}
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-lazarus-text">{card.label}</p>
                <p className="mt-1 text-xs leading-5 text-lazarus-muted">{card.subtitle}</p>
              </div>
              <span className="rounded-full bg-lazarus-surface/80 px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-lazarus-text">
                {card.status}
              </span>
            </div>

            <div className="mt-4 flex items-end justify-between gap-4">
              <div>
                <p className="font-mono text-[1.7rem] font-semibold tracking-[-0.05em] text-lazarus-text">
                  {formatResourceValue(card)}
                </p>
                <p className="mt-1 text-xs uppercase tracking-[0.18em] text-lazarus-muted">
                  Trend {card.trend}
                </p>
              </div>
              <div className="min-w-[7rem]">
                <div className="h-2 rounded-full bg-lazarus-surface/80">
                  <div
                    className={`h-2 rounded-full ${
                      card.status === 'critical'
                        ? 'bg-lazarus-critical'
                        : card.status === 'warning'
                          ? 'bg-lazarus-warning'
                          : 'bg-lazarus-normal'
                    }`}
                    style={{ width: `${card.utilization_percent}%` }}
                  />
                </div>
                <p className="mt-2 text-right text-xs text-lazarus-muted">
                  {card.utilization_percent}% reserve remaining
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="chart-shell rounded-[1.5rem] border border-lazarus-border/80 bg-lazarus-surface/80 p-4">
        <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="section-label">Projected depletion curve</p>
            <p className="mt-1 text-sm text-lazarus-muted">
              Forecast reacts to current crisis level, staffing load, and ICU occupancy.
            </p>
          </div>
        </div>

        <div className="h-[20rem]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={forecast}>
              <CartesianGrid stroke="rgba(148, 163, 184, 0.16)" strokeDasharray="3 3" />
              <XAxis dataKey="time_label" stroke="rgb(var(--color-lazarus-muted))" fontSize={12} />
              <YAxis stroke="rgb(var(--color-lazarus-muted))" fontSize={12} />
              <Tooltip
                contentStyle={{
                  borderRadius: '18px',
                  border: '1px solid rgba(148, 163, 184, 0.16)',
                  background: 'rgba(10, 20, 24, 0.94)',
                  color: '#f8fafc',
                }}
              />
              <Line
                type="monotone"
                dataKey="oxygen_network_percent"
                stroke="#0891B2"
                strokeWidth={3}
                dot={false}
                name="Oxygen"
              />
              <Line
                type="monotone"
                dataKey="staff_load_percent"
                stroke="#059669"
                strokeWidth={3}
                dot={false}
                name="Staff load"
              />
              <Line
                type="monotone"
                dataKey="ventilator_usage_percent"
                stroke="#D65C5C"
                strokeWidth={3}
                dot={false}
                name="Ventilator usage"
              />
              <Line
                type="monotone"
                dataKey="vasopressor_stock_percent"
                stroke="#C08B3E"
                strokeWidth={3}
                dot={false}
                name="Vasopressor"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </section>
  )
}
