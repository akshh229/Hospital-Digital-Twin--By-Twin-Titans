import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import ICUBedHeatmap from './ICUBedHeatmap'

function renderHeatmap(
  availabilityFilter: 'all' | 'available' | 'occupied',
  selectedZone: string | null
) {
  return render(
    <MemoryRouter>
      <ICUBedHeatmap
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
            assignment_reason: 'Critical acuity routing',
            patient: {
              patient_id: 'patient-1',
              patient_raw_id: 'SJ-1001',
              patient_name: 'Aarav Patel',
              age: 56,
              ward: 'ICU North',
              parity_flag: 'even',
              last_bpm: 122,
              last_oxygen: 89,
              has_active_alert: true,
              risk_score: 88,
              risk_label: 'Critical',
              recommended_unit: 'ICU',
              risk_reasons: ['Telemetry alert'],
            },
          },
          {
            bed_id: 'ICU-03',
            zone: 'South Pod',
            status: 'occupied',
            assignment_reason: 'High acuity routing',
            patient: {
              patient_id: 'patient-2',
              patient_raw_id: 'SJ-1002',
              patient_name: 'Maya Rao',
              age: 42,
              ward: 'ICU South',
              parity_flag: 'odd',
              last_bpm: 104,
              last_oxygen: 94,
              has_active_alert: false,
              risk_score: 70,
              risk_label: 'High',
              recommended_unit: 'ICU',
              risk_reasons: ['Acuity watch'],
            },
          },
        ]}
        triageQueue={[]}
        availabilityFilter={availabilityFilter}
        selectedZone={selectedZone}
      />
    </MemoryRouter>
  )
}

describe('ICUBedHeatmap', () => {
  it('filters visible beds by availability', () => {
    renderHeatmap('available', null)

    expect(screen.getByText('ICU-01')).toBeInTheDocument()
    expect(screen.queryByText('ICU-02')).not.toBeInTheDocument()
    expect(screen.queryByText('ICU-03')).not.toBeInTheDocument()
  })

  it('filters visible beds by zone and shows an empty state when nothing matches', () => {
    const { rerender } = renderHeatmap('all', 'South Pod')

    expect(screen.getByText('ICU-03')).toBeInTheDocument()
    expect(screen.queryByText('ICU-01')).not.toBeInTheDocument()
    expect(screen.queryByText('ICU-02')).not.toBeInTheDocument()

    rerender(
      <MemoryRouter>
        <ICUBedHeatmap
          beds={[
            {
              bed_id: 'ICU-01',
              zone: 'North Pod',
              status: 'available',
              assignment_reason: 'Ready for incoming critical admissions',
              patient: null,
            },
          ]}
          triageQueue={[]}
          availabilityFilter="occupied"
          selectedZone="North Pod"
        />
      </MemoryRouter>
    )

    expect(
      screen.getByText(/No beds match the current room availability filter/i)
    ).toBeInTheDocument()
  })
})
