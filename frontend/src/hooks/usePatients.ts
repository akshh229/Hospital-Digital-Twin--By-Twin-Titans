import { useQuery } from '@tanstack/react-query'
import api from '../api/client'
import type { Patient } from '../types'

export function usePatients() {
  return useQuery({
    queryKey: ['patients'],
    queryFn: async () => {
      const { data } = await api.get<Patient[]>('/patients')
      return data
    },
  })
}

export function usePatient(patientId: string) {
  return useQuery({
    queryKey: ['patient', patientId],
    queryFn: async () => {
      const { data } = await api.get<Patient>(`/patients/${patientId}`)
      return data
    },
    enabled: !!patientId,
  })
}
