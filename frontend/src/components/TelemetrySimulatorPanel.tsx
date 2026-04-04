import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import type {
  RealtimeConnectionState,
  TelemetrySimulationResponse,
} from '../types'

interface TelemetrySimulatorPanelProps {
  patientId: string
  connectionState: RealtimeConnectionState
}

const abnormalPreset = { bpm: 118, oxygen: 96 }
const normalPreset = { bpm: 78, oxygen: 99 }

export default function TelemetrySimulatorPanel({
  patientId,
  connectionState,
}: TelemetrySimulatorPanelProps) {
  const queryClient = useQueryClient()
  const [bpm, setBpm] = useState(abnormalPreset.bpm)
  const [oxygen, setOxygen] = useState(abnormalPreset.oxygen)
  const [feedback, setFeedback] = useState<string | null>(null)

  if (!import.meta.env.DEV) {
    return null
  }

  const simulateTelemetry = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<TelemetrySimulationResponse>(
        '/dev/simulate-telemetry',
        {
          patient_id: patientId,
          bpm,
          oxygen,
        }
      )
      return data
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ['patient', patientId] })
      queryClient.invalidateQueries({ queryKey: ['patients'] })
      queryClient.invalidateQueries({ queryKey: ['vitals', patientId] })
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['alertHistory', patientId] })

      const adjustmentNote = result.adjusted_for_identity
        ? ` Requested BPM ${result.requested_bpm} was adjusted to ${result.applied_bpm} to preserve this patient's parity mapping.`
        : ''

      setFeedback(
        `Sample saved at ${new Date(result.timestamp).toLocaleTimeString([], {
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit',
        })}.${adjustmentNote}`
      )
    },
  })

  const feedHint =
    connectionState === 'live'
      ? 'The realtime socket is live, so the patient cards should react immediately.'
      : connectionState === 'reconnecting'
        ? 'The realtime socket is reconnecting. Query refresh will still surface the sample.'
        : connectionState === 'connecting'
          ? 'The realtime socket is still connecting. Query refresh will surface the sample first.'
          : 'The realtime socket is offline. This panel still writes data so you can QA non-realtime states.'

  return (
    <section className="card mb-6 border border-dashed border-lazarus-border/40 bg-lazarus-surface/50">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-sm font-semibold uppercase tracking-wide text-lazarus-text">
            Developer Telemetry Simulator
          </h2>
          <p className="mt-1 max-w-2xl text-sm text-lazarus-muted">
            Inject one vitals sample for demos and QA without touching the database manually.
          </p>
        </div>
        <span className="rounded-full bg-lazarus-surface-low px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-lazarus-warning ring-1 ring-lazarus-warning/20">
          Dev Only
        </span>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,auto)] lg:items-end">
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="rounded-xl bg-lazarus-surface-low/80 p-4 ring-1 ring-lazarus-border/25">
            <span className="vitals-label">Heart Rate (BPM)</span>
            <input
              type="number"
              min={20}
              max={220}
              value={bpm}
              onChange={(event) => setBpm(Number(event.target.value))}
              className="mt-3 w-full rounded-lg border border-lazarus-border bg-lazarus-surface px-3 py-2 font-mono text-lg text-lazarus-text outline-none transition focus:border-lazarus-accent focus:ring-2 focus:ring-lazarus-accent/20"
            />
          </label>

          <label className="rounded-xl bg-lazarus-surface-low/80 p-4 ring-1 ring-lazarus-border/25">
            <span className="vitals-label">SpO2 (%)</span>
            <input
              type="number"
              min={50}
              max={100}
              value={oxygen}
              onChange={(event) => setOxygen(Number(event.target.value))}
              className="mt-3 w-full rounded-lg border border-lazarus-border bg-lazarus-surface px-3 py-2 font-mono text-lg text-lazarus-text outline-none transition focus:border-lazarus-accent focus:ring-2 focus:ring-lazarus-accent/20"
            />
          </label>
        </div>

        <div className="flex flex-wrap gap-2 lg:justify-end">
          <button
            type="button"
            onClick={() => {
              setBpm(abnormalPreset.bpm)
              setOxygen(abnormalPreset.oxygen)
            }}
            className="rounded-lg border border-lazarus-critical/25 bg-[rgba(216,92,92,0.1)] px-3 py-2 text-sm font-semibold text-lazarus-critical transition hover:-translate-y-0.5"
          >
            Load alert preset
          </button>
          <button
            type="button"
            onClick={() => {
              setBpm(normalPreset.bpm)
              setOxygen(normalPreset.oxygen)
            }}
            className="rounded-lg border border-lazarus-normal/25 bg-[rgba(47,155,115,0.1)] px-3 py-2 text-sm font-semibold text-lazarus-normal transition hover:-translate-y-0.5"
          >
            Load normal preset
          </button>
          <button
            type="button"
            onClick={() => simulateTelemetry.mutate()}
            disabled={simulateTelemetry.isPending}
            className="rounded-lg bg-lazarus-accent px-4 py-2 text-sm font-semibold text-white transition hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {simulateTelemetry.isPending ? 'Injecting sample...' : 'Inject sample'}
          </button>
        </div>
      </div>

      <div className="mt-4 rounded-xl bg-lazarus-surface/94 p-4 ring-1 ring-lazarus-border/70">
        <p className="text-sm font-semibold text-lazarus-text">QA note</p>
        <p className="mt-1 text-sm text-lazarus-muted">{feedHint}</p>
      </div>

      {(feedback || simulateTelemetry.isError) && (
        <div
          aria-live="polite"
          className={`mt-4 rounded-xl p-4 text-sm ring-1 ${
            simulateTelemetry.isError
              ? 'bg-[rgba(216,92,92,0.1)] text-lazarus-critical ring-lazarus-critical/20'
              : 'bg-[rgba(47,155,115,0.1)] text-lazarus-normal ring-lazarus-normal/20'
          }`}
        >
          {simulateTelemetry.isError
            ? 'The sample could not be inserted. Check the backend logs for the exact error.'
            : feedback}
        </div>
      )}
    </section>
  )
}
