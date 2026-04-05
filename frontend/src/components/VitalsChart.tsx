import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea, Legend } from 'recharts'
import type { VitalsDataPoint } from '../types'

interface VitalsChartProps {
  data: VitalsDataPoint[]
  title?: string
  showBpm?: boolean
  showOxygen?: boolean
}

export default function VitalsChart({ data, title, showBpm = true, showOxygen = true }: VitalsChartProps) {
  const chartData = data.map((d) => ({
    ...d,
    time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  }))
  const latestPoint = chartData[chartData.length - 1]
  const chartPalette = {
    grid: 'rgb(var(--color-lazarus-border) / 0.26)',
    axis: 'rgb(var(--color-lazarus-muted) / 0.86)',
    tooltipBg: 'rgb(var(--color-lazarus-surface-low) / 0.96)',
    tooltipBorder: '1px solid rgb(var(--color-lazarus-border) / 0.56)',
    tooltipText: 'rgb(var(--color-lazarus-text) / 0.96)',
    tooltipShadow: '0 18px 40px rgb(3 8 15 / 0.28)',
    oxygenLine: 'rgb(var(--color-lazarus-info) / 0.84)',
    oxygenDot: 'rgb(var(--color-lazarus-info))',
    oxygenBand: 'rgb(var(--color-lazarus-info))',
    bpmLine: 'rgb(var(--color-lazarus-critical) / 0.9)',
    bpmDot: 'rgb(var(--color-lazarus-critical))',
    safeZone: 'rgb(var(--color-lazarus-normal) / 0.12)',
  }

  return (
    <div className="card chart-shell">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="section-label">Telemetry lane</p>
          {title && <h3 className="mt-2 font-display text-[2rem] leading-none tracking-[-0.03em] text-lazarus-text">{title}</h3>}
          <p className="mt-3 text-sm text-lazarus-muted">
            Streaming bedside vitals with continuity cues for command-center and patient-level review.
          </p>
        </div>
        {latestPoint && (
          <div className="signal-pill rounded-full bg-lazarus-surface/94 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-lazarus-muted">
            Latest sample {latestPoint.time}
          </div>
        )}
      </div>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke={chartPalette.grid} strokeOpacity={0.9} vertical={false} />
          <XAxis
            dataKey="time"
            stroke={chartPalette.axis}
            tick={{ fontSize: 11 }}
            interval="preserveStartEnd"
          />
          {showBpm && (
            <YAxis
              yAxisId="bpm"
              domain={[40, 160]}
              stroke={chartPalette.axis}
              tick={{ fontSize: 11 }}
              label={{ value: 'BPM', angle: -90, position: 'insideLeft', fill: chartPalette.axis, fontSize: 11 }}
            />
          )}
          {showOxygen && (
            <YAxis
              yAxisId="oxygen"
              orientation="right"
              domain={[85, 100]}
              stroke={chartPalette.axis}
              tick={{ fontSize: 11 }}
              label={{ value: 'SpO2%', angle: 90, position: 'insideRight', fill: chartPalette.axis, fontSize: 11 }}
            />
          )}
          <Tooltip
            contentStyle={{
              backgroundColor: chartPalette.tooltipBg,
              backdropFilter: 'blur(10px)',
              border: chartPalette.tooltipBorder,
              borderRadius: '14px',
              color: chartPalette.tooltipText,
              boxShadow: chartPalette.tooltipShadow,
            }}
          />
          <Legend wrapperStyle={{ color: chartPalette.axis, fontSize: '12px' }} />

          {/* BPM safe zone */}
          {showBpm && (
            <>
              <ReferenceArea yAxisId="bpm" y1={60} y2={100} fill={chartPalette.safeZone} />
              <ReferenceLine yAxisId="bpm" y={60} stroke={chartPalette.safeZone} strokeDasharray="5 5" strokeOpacity={0.75} />
              <ReferenceLine yAxisId="bpm" y={100} stroke={chartPalette.safeZone} strokeDasharray="5 5" strokeOpacity={0.75} />
            </>
          )}

          {/* SpO2 safe zone */}
          {showOxygen && (
            <ReferenceArea yAxisId="oxygen" y1={95} y2={100} fill={chartPalette.oxygenBand} fillOpacity={0.1} />
          )}

          {showBpm && (
            <Line
              yAxisId="bpm"
              type="monotone"
              dataKey="bpm"
              stroke={chartPalette.bpmLine}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5, strokeWidth: 0, fill: chartPalette.bpmDot }}
              isAnimationActive
              animationDuration={450}
              animationEasing="ease-out"
              connectNulls
              name="BPM"
            />
          )}
          {showOxygen && (
            <Line
              yAxisId="oxygen"
              type="monotone"
              dataKey="oxygen"
              stroke={chartPalette.oxygenLine}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 5, strokeWidth: 0, fill: chartPalette.oxygenDot }}
              isAnimationActive
              animationDuration={450}
              animationEasing="ease-out"
              name="SpO2 (reconstructed)"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
