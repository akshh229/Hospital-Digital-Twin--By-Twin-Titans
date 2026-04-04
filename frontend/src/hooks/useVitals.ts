import { useQuery } from '@tanstack/react-query'
import api from '../api/client'
import type { VitalsResponse } from '../types'

interface UseVitalsOptions {
  refetchInterval?: number | false
}

export function useVitals(
  patientId: string,
  hours: number = 24,
  options: UseVitalsOptions = {}
) {
  return useQuery({
    queryKey: ['vitals', patientId, hours],
    queryFn: async () => {
      const { data } = await api.get<VitalsResponse>(`/patients/${patientId}/vitals`, {
        params: { hours },
      })
      return data
    },
    enabled: !!patientId,
    refetchInterval: options.refetchInterval ?? 5000,
  })
}
