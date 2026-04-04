import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import api from '../api/client'
import PatientAlertPanel from './PatientAlertPanel'

vi.mock('../api/client', () => ({
  default: {
    get: vi.fn(),
    patch: vi.fn(),
  },
}))

const mockedApi = vi.mocked(api, true)

function renderPanel() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })

  return render(
    <MemoryRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <QueryClientProvider client={queryClient}>
        <PatientAlertPanel patientId="patient-1" />
      </QueryClientProvider>
    </MemoryRouter>
  )
}

describe('PatientAlertPanel', () => {
  beforeEach(() => {
    let alertsRequestCount = 0
    let historyRequestCount = 0

    mockedApi.get.mockImplementation(async (url: string) => {
      if (url === '/alerts') {
        alertsRequestCount += 1

        return {
          data:
            alertsRequestCount === 1
              ? [
                  {
                    id: 7,
                    patient_id: 'patient-1',
                    alert_type: 'critical_vitals',
                    opened_at: '2026-03-29T12:00:00.000Z',
                    last_bpm: 118,
                    last_oxygen: 96,
                    status: 'open',
                    consecutive_abnormal_count: 2,
                    patient_name: 'John Anderson',
                    age: 83,
                    ward: 'Ward-4',
                  },
                ]
              : [],
        }
      }

      if (url === '/alerts/history/patient-1') {
        historyRequestCount += 1

        return {
          data:
            historyRequestCount === 1
              ? []
              : [
                  {
                    id: 7,
                    opened_at: '2026-03-29T12:00:00.000Z',
                    closed_at: '2026-03-29T12:02:00.000Z',
                    duration_minutes: 2,
                    last_bpm: 118,
                    last_oxygen: 96,
                    status: 'acknowledged',
                  },
                ],
        }
      }

      throw new Error(`Unhandled GET ${url}`)
    })

    mockedApi.patch.mockResolvedValue({
      data: {
        status: 'acknowledged',
        alert_id: 7,
      },
    })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('acknowledges an alert and refreshes the UI state from API data', async () => {
    const user = userEvent.setup()

    renderPanel()

    expect(
      await screen.findByText('Alert acknowledgement available')
    ).toBeInTheDocument()

    await user.click(
      screen.getByRole('button', { name: /acknowledge alert/i })
    )

    await waitFor(() => {
      expect(mockedApi.patch).toHaveBeenCalledWith('/alerts/7/acknowledge')
    })

    expect(
      await screen.findByText('No active critical alert for this patient.')
    ).toBeInTheDocument()

    expect(await screen.findByText('Alert #7')).toBeInTheDocument()
    expect(screen.getByText('Acknowledged')).toBeInTheDocument()
  })
})
