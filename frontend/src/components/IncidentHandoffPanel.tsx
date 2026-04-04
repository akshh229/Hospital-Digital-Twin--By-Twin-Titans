import { useState } from 'react'
import type { IncidentHandoff } from '../types'

interface IncidentHandoffPanelProps {
  handoff: IncidentHandoff
}

function toneForStatus(status: IncidentHandoff['status']) {
  if (status === 'critical') {
    return 'badge-critical'
  }
  if (status === 'watch') {
    return 'badge-warning'
  }
  return 'badge-normal'
}

function formatTimestamp(timestamp: string) {
  return new Date(timestamp).toLocaleString([], {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    year: 'numeric',
    month: 'short',
    day: '2-digit',
  })
}

function saveBlob(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

export default function IncidentHandoffPanel({
  handoff,
}: IncidentHandoffPanelProps) {
  const [copyState, setCopyState] = useState<'idle' | 'copied' | 'error'>('idle')

  async function handleCopyMarkdown() {
    try {
      if (!navigator.clipboard?.writeText) {
        throw new Error('Clipboard API unavailable')
      }

      await navigator.clipboard.writeText(handoff.markdown)
      setCopyState('copied')
    } catch {
      setCopyState('error')
    }
  }

  function handleDownloadMarkdown() {
    saveBlob(`${handoff.export_filename}.md`, handoff.markdown, 'text/markdown;charset=utf-8')
  }

  function handleDownloadJson() {
    saveBlob(
      `${handoff.export_filename}.json`,
      JSON.stringify(handoff, null, 2),
      'application/json;charset=utf-8'
    )
  }

  return (
    <section className="card space-y-5">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="section-label">Incident handoff</p>
          <h2 className="mt-2 font-display text-[2rem] font-semibold leading-none tracking-[-0.03em] text-lazarus-text">
            Export-ready command summary
          </h2>
          <p className="mt-3 text-sm leading-6 text-lazarus-muted">
            Package the live ICU state into a handoff that can move to the next shift,
            a demo reviewer, or a post-incident note without leaving the command center.
          </p>
        </div>
        <span className={toneForStatus(handoff.status)}>{handoff.status_label}</span>
      </div>

      <div className="rounded-[1.45rem] border border-lazarus-border/70 bg-lazarus-surface/80 p-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
              Current package
            </p>
            <h3 className="mt-2 text-lg font-semibold text-lazarus-text">{handoff.title}</h3>
          </div>
          <span className="dossier-chip">{formatTimestamp(handoff.generated_at)}</span>
        </div>

        <p className="mt-3 text-sm leading-6 text-lazarus-muted">{handoff.summary}</p>

        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          {handoff.command_snapshot.map((metric) => (
            <div
              key={metric.key}
              className="rounded-[1.2rem] bg-lazarus-surface/85 px-4 py-3"
            >
              <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
                {metric.label}
              </p>
              <p className="mt-1 text-sm font-semibold text-lazarus-text">{metric.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        <div className="rounded-[1.35rem] border border-lazarus-border/70 bg-lazarus-surface/75 p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
            Immediate risks
          </p>
          <div className="mt-3 space-y-2">
            {handoff.immediate_risks.map((risk, index) => (
              <p key={`${risk}-${index}`} className="text-sm leading-6 text-lazarus-text">
                {risk}
              </p>
            ))}
          </div>
        </div>

        <div className="rounded-[1.35rem] border border-lazarus-border/70 bg-lazarus-surface/75 p-4">
          <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
            Recommended next steps
          </p>
          <div className="mt-3 space-y-2">
            {handoff.next_steps.map((step, index) => (
              <p key={`${step}-${index}`} className="text-sm leading-6 text-lazarus-text">
                {step}
              </p>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-[1.35rem] border border-lazarus-border/70 bg-lazarus-surface/75 p-4">
        <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-lazarus-muted">
          Active interventions and recent actions
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          {handoff.active_interventions.length > 0 ? (
            handoff.active_interventions.map((item, index) => (
              <span key={`${item}-${index}`} className="dossier-chip">
                {item}
              </span>
            ))
          ) : (
            <span className="dossier-chip">No active intervention modifiers</span>
          )}
        </div>
        <div className="mt-4 space-y-2">
          {handoff.recent_actions.map((action, index) => (
            <p key={`${action}-${index}`} className="text-sm leading-6 text-lazarus-muted">
              {action}
            </p>
          ))}
        </div>
      </div>

      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          className="rounded-full border border-lazarus-info bg-lazarus-info/10 px-4 py-2 text-sm font-semibold text-lazarus-info transition-transform hover:-translate-y-0.5"
          onClick={handleCopyMarkdown}
        >
          {copyState === 'copied'
            ? 'Markdown copied'
            : copyState === 'error'
              ? 'Copy unavailable'
              : 'Copy markdown'}
        </button>
        <button
          type="button"
          className="rounded-full border border-lazarus-border bg-lazarus-surface px-4 py-2 text-sm font-semibold text-lazarus-text transition-transform hover:-translate-y-0.5"
          onClick={handleDownloadMarkdown}
        >
          Download markdown
        </button>
        <button
          type="button"
          className="rounded-full border border-lazarus-border bg-lazarus-surface px-4 py-2 text-sm font-semibold text-lazarus-text transition-transform hover:-translate-y-0.5"
          onClick={handleDownloadJson}
        >
          Download JSON
        </button>
      </div>

      <p className="text-xs leading-5 text-lazarus-muted">
        Export package: <span className="font-mono">{handoff.export_filename}</span>. The
        markdown version is optimized for shift notes and docs, while JSON preserves the
        structured incident state.
      </p>
    </section>
  )
}
