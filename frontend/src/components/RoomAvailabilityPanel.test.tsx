import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import RoomAvailabilityPanel from './RoomAvailabilityPanel'

describe('RoomAvailabilityPanel', () => {
  it('renders live availability counts and emits filter changes', async () => {
    const user = userEvent.setup()
    const onAvailabilityFilterChange = vi.fn()
    const onZoneChange = vi.fn()

    render(
      <RoomAvailabilityPanel
        beds={[
          {
            bed_id: 'ICU-01',
            zone: 'North Pod',
            status: 'available',
            assignment_reason: 'Ready for incoming critical admissions',
            patient: null,
          },
          {
            bed_id: 'ICU-02',
            zone: 'North Pod',
            status: 'occupied',
            assignment_reason: 'Alert escalation routing',
            patient: {
              patient_id: 'patient-1',
              patient_raw_id: 'SJ-1001',
              patient_name: 'Aarav Patel',
              age: 56,
              ward: 'ICU North',
              parity_flag: 'even',
              last_bpm: 118,
              last_oxygen: 91,
              has_active_alert: true,
              risk_score: 82,
              risk_label: 'Critical',
              recommended_unit: 'ICU',
              risk_reasons: ['Telemetry alert'],
            },
          },
          {
            bed_id: 'ICU-03',
            zone: 'South Pod',
            status: 'available',
            assignment_reason: 'Ready for incoming critical admissions',
            patient: null,
          },
        ]}
        triageQueue={[
          {
            patient_id: 'queue-1',
            patient_name: 'Maya Rao',
            patient_raw_id: 'SJ-1002',
            risk_score: 75,
            risk_label: 'High',
            queue_reason: 'ICU demand exceeds live capacity',
            recommended_unit: 'ICU',
            risk_reasons: ['Overflow pressure'],
          },
        ]}
        availabilityFilter="all"
        selectedZone={null}
        onAvailabilityFilterChange={onAvailabilityFilterChange}
        onZoneChange={onZoneChange}
      />
    )

    expect(screen.getByText('Open bed command view')).toBeInTheDocument()
    expect(screen.getByText('ICU-01')).toBeInTheDocument()
    expect(screen.getByText('ICU-03')).toBeInTheDocument()
    expect(screen.getByText('North Pod 1 ready')).toBeInTheDocument()
    expect(screen.getByText('South Pod 1 ready')).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: 'Available now' }))
    expect(onAvailabilityFilterChange).toHaveBeenCalledWith('available')

    await user.click(screen.getByRole('button', { name: 'South Pod 1 ready' }))
    expect(onZoneChange).toHaveBeenCalledWith('South Pod')
  })
})
