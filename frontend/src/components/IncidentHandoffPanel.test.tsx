import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import IncidentHandoffPanel from './IncidentHandoffPanel'

describe('IncidentHandoffPanel', () => {
  it('renders handoff data and export actions', () => {
    render(
      <IncidentHandoffPanel
        handoff={{
          title: 'Oxygen network degradation incident handoff',
          generated_at: '2026-04-05T09:05:00.000Z',
          status: 'critical',
          status_label: 'Critical pressure',
          scenario_label: 'Oxygen network degradation',
          summary:
            'Oxygen network degradation is currently running with ICU occupancy at 12/14 beds, 2 patients in overflow, and 1 active telemetry alert.',
          command_snapshot: [
            {
              key: 'icu_occupied',
              label: 'ICU occupied',
              value: '12/14 beds',
            },
            {
              key: 'overflow_patients',
              label: 'Overflow queue',
              value: '2 patients',
            },
          ],
          immediate_risks: [
            '2 patients still exceed live ICU routing capacity.',
            'Oxygen network is at 28% and trending falling.',
          ],
          active_interventions: [
            'Oxygen reserve buffer (+12%): Respiratory reserve support is currently lifting the oxygen network model.',
          ],
          recent_actions: ['09:02 UTC | Applied oxygen reserve protection'],
          next_steps: [
            'Open surge beds or accelerate step-down transfers (Owner: Hospital ops lead)',
          ],
          export_filename: 'icu-incident-handoff-20260405-090500',
          markdown: '# Oxygen network degradation incident handoff',
        }}
      />
    )

    expect(screen.getByText('Export-ready command summary')).toBeInTheDocument()
    expect(screen.getByText('Critical pressure')).toBeInTheDocument()
    expect(screen.getByText('Oxygen network degradation incident handoff')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Download markdown' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Download JSON' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Copy markdown' })).toBeInTheDocument()
    expect(screen.getByText('icu-incident-handoff-20260405-090500')).toBeInTheDocument()
  })
})
