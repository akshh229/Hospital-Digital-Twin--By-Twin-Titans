import { useQuery } from '@tanstack/react-query'

interface HealthResponse {
  status: string
  service: string
  version: string
}

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: async () => {
      const response = await fetch('/health')

      if (!response.ok) {
        throw new Error(`Health check failed with status ${response.status}`)
      }

      return (await response.json()) as HealthResponse
    },
    refetchInterval: 15000,
    staleTime: 10000,
    retry: 1,
  })
}
