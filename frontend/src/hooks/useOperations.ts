import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import api from '../api/client'
import type {
  OperationsOverview,
  OpsSnapshotMessage,
  SimulationControlRequest,
} from '../types'
import { useManagedWebSocket } from './useManagedWebSocket'

export const operationsOverviewQueryKey = ['operationsOverview'] as const

export function useOperationsOverview() {
  return useQuery({
    queryKey: operationsOverviewQueryKey,
    queryFn: async () => {
      const { data } = await api.get<OperationsOverview>('/ops/overview')
      return data
    },
    refetchInterval: 12000,
  })
}

export function useOperationsRealtime(enabled = true) {
  const queryClient = useQueryClient()

  return useManagedWebSocket<OpsSnapshotMessage>({
    path: '/ws/ops/overview',
    enabled,
    onMessage: (message) => {
      if (message.type !== 'ops_snapshot') {
        return
      }

      queryClient.setQueryData(operationsOverviewQueryKey, message.overview)
    },
  })
}

export function useSimulationControl() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (payload: SimulationControlRequest) => {
      const { data } = await api.post<OperationsOverview>('/ops/control', payload)
      return data
    },
    onSuccess: (overview) => {
      queryClient.setQueryData(operationsOverviewQueryKey, overview)
      queryClient.invalidateQueries({ queryKey: ['alerts'] })
      queryClient.invalidateQueries({ queryKey: ['patients'] })
    },
  })
}
