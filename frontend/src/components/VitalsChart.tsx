import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceArea, Legend } from 'recharts'
import type { VitalsDataPoint } from '../types'
import { useTheme } from '../theme/ThemeProvider'

interface VitalsChartProps {
  data: VitalsDataPoint[]
  title?: string
  showBpm?: boolean
  showOxygen?: boolean
}

export default function VitalsChart({ data, title, showBpm = true, showOxygen = true }: VitalsChartProps) {
  const { theme } = useTheme()
  const chartData = data.map((d) => ({
    ...d,
    time: new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  }))
  const latestPoint = chartData[chartData.length - 1]
  const chartPalette =
    theme === 'navy'
      ? {
          grid: '#2b3a4f',
          axis: '#94a8bf',
          tooltipBg: 'rgba(17, 28, 45, 0.96)',
          tooltipBorder: '1px solid rgba(43, 58, 79, 0.95)',
          tooltipText: '#eaf0f7',
          tooltipShadow: '0 18px 40px rgba(3, 10, 18, 0.42)',
          oxygenLine: '#9db8d6',
          oxygenDot: '#dbe8f7',
          oxygenBand: '#7fa7c9',
          bpmLine: '#f26d6d',
          bpmDot: '#ffd6d6',
        }
      : {
          grid: '#d7dee6',
          axis: '#60758a',
          tooltipBg: 'rgba(255, 255, 255, 0.97)',
          tooltipBorder: '1px solid rgba(215, 222, 230, 0.95)',
          tooltipText: '#18212b',
          tooltipShadow: '0 18px 40px rgba(43, 58, 79, 0.12)',
          oxygenLine: '#4f6d8a',
          oxygenDot: '#b8c8d8',
          oxygenBand: '#6b84a0',
          bpmLine: '#d85c5c',
          bpmDot: '#ffd4d4',
        }

  return (
    <div className="card chart-shell">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="section-label">Recovered telemetry</p>
          {title && <h3 className="mt-2 font-display text-[2rem] leading-none tracking-[-0.03em] text-lazarus-text">{title}</h3>}
          <p className="mt-3 text-sm text-lazarus-muted">
            Streaming decoded BPM with reconstructed oxygen continuity across dropped frames.
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
              boxShadow: chartPalette.tooltipShadow
            }}
          />
          <Legend />

          {/* BPM safe zone */}
          {showBpm && (
            <>
              <ReferenceArea yAxisId="bpm" y1={60} y2={100} fill="#10b981" fillOpacity={0.1} />
              <ReferenceLine yAxisId="bpm" y={60} stroke="#10b981" strokeDasharray="5 5" strokeOpacity={0.5} />
              <ReferenceLine yAxisId="bpm" y={100} stroke="#10b981" strokeDasharray="5 5" strokeOpacity={0.5} />
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
