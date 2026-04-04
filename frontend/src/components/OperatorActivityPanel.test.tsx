import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import OperatorActivityPanel from './OperatorActivityPanel'

describe('OperatorActivityPanel', () => {
  it('renders the latest operator posture and recent activity entries', () => {
    render(
      <OperatorActivityPanel
        simulation={{
          is_paused: false,
          speed: 1.5,
          active_scenario: 'oxygen_shortage',
          crisis_level: 2,
          crisis_label: 'Oxygen network degradation',
          virtual_admissions: 2,
          active_interventions: [
            {
              id: 'protect-oxygen-reserve',
              label: 'Oxygen reserve buffer',
              value: '+12%',
              effect: 'Respiratory reserve support is currently lifting the oxygen network model.',
              can_step_down: false,
              step_down_label: null,
              can_clear: true,
              clear_label: 'Clear reserve buffer',
            },
          ],
          updated_at: '2026-04-05T09:03:00.000Z',
          last_action: 'set_speed',
          last_action_label: 'Set speed to 1.5x',
          last_action_at: '2026-04-05T09:02:00.000Z',
        }}
        activity={[
          {
            id: 'evt-speed',
            timestamp: '2026-04-05T09:02:00.000Z',
            action_key: 'set_speed',
            action_label: 'Set speed to 1.5x',
            event_type: 'simulation',
            severity: 'warning',
            title: 'Playback speed set to 1.5x',
            description: 'Command center updated the simulation speed to stress-test response timing.',
            intervention_id: null,
            scenario_label: 'Oxygen network degradation',
            speed: 1.5,
          },
          {
            id: 'evt-oxygen',
            timestamp: '2026-04-05T09:01:00.000Z',
            action_key: 'apply_intervention',
            action_label: 'Applied oxygen reserve protection',
            event_type: 'intervention',
            severity: 'warning',
            title: 'Oxygen reserve protected',
            description: 'Respiratory reserve buffers were applied to stabilize the oxygen network.',
            intervention_id: 'protect-oxygen-reserve',
            scenario_label: 'Oxygen network degradation',
            speed: null,
          },
        ]}
      />
    )

    expect(
      screen.getByRole('heading', { name: 'Set speed to 1.5x' })
    ).toBeInTheDocument()
    expect(screen.getByText('Command audit trail')).toBeInTheDocument()
    expect(screen.getByText('Applied oxygen reserve protection')).toBeInTheDocument()
    expect(screen.getByText('Oxygen reserve')).toBeInTheDocument()
    expect(screen.getAllByText('1.5x').length).toBeGreaterThan(0)
  })
})
