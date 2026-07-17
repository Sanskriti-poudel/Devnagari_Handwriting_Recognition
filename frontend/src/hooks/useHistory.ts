import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { historyService } from '@/services/history.service'
import type { HistoryFilters } from '@/types'

export function useHistoryList(filters: HistoryFilters) {
  return useQuery({
    queryKey: ['history', filters],
    queryFn: () => historyService.list(filters),
    placeholderData: (prev) => prev,
  })
}

export function useDeleteHistory() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: historyService.remove,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['history'] })
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}
