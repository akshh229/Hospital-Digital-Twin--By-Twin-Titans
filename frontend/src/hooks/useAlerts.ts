import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import type { Alert, AlertHistory } from '../types'

export function useAlerts() {
  return useQuery({
    queryKey: ['alerts'],
    queryFn: async () => {
      const { data } = await api.get<Alert[]>('/alerts')
      return data
    },
    refetchInterval: 5000,
  })
}

export function useAlertHistory(patientId: string) {
  return useQuery({
    queryKey: ['alertHistory', patientId],
    queryFn: async () => {
      const { data } = await api.get<AlertHistory[]>(`/alerts/history/${patientId}`)
      return data
    },
    enabled: !!patientId,
  })
}

interface AcknowledgeAlertPayload {
  alertId: number
  patientId: string
}

export function useAcknowledgeAlert() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ alertId }: AcknowledgeAlertPayload) => {
      const { data } = await api.patch(`/alerts/${alertId}/acknowledge`)
      return data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['patients'] })
      queryClient.invalidateQueries({ queryKey: ['patient', variables.patientId] })
      queryClient.invalidateQueries({ queryKey: ['alertHistory', variables.patientId] })
    },
  })
}
