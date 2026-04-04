import { useQueryClient } from '@tanstack/react-query'
import { useManagedWebSocket } from './useManagedWebSocket'
import type { AlertsSnapshotMessage, PatientsSnapshotMessage } from '../types'

type OverviewRealtimeMessage =
  | AlertsSnapshotMessage
  | PatientsSnapshotMessage

export function useOverviewRealtime() {
  const queryClient = useQueryClient()

  return useManagedWebSocket<OverviewRealtimeMessage>({
    path: '/ws/overview',
    onMessage: (message) => {
      if (message.type === 'patients_snapshot') {
        queryClient.setQueryData(['patients'], message.patients)
        return
      }

      queryClient.setQueryData(['alerts'], message.alerts)
    },
  })
}
