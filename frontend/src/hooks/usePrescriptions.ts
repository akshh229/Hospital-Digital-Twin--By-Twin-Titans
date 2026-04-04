import { useQuery } from '@tanstack/react-query'
import api from '../api/client'
import type { Prescription } from '../types'

export function usePrescriptions(patientId: string) {
  return useQuery({
    queryKey: ['prescriptions', patientId],
    queryFn: async () => {
      const { data } = await api.get<Prescription[]>(`/patients/${patientId}/prescriptions`)
      return data
    },
    enabled: !!patientId,
  })
}
