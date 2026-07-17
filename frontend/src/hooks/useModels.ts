import { useQuery } from '@tanstack/react-query'
import { modelsService } from '@/services/models.service'

export function useModels() {
  return useQuery({ queryKey: ['models'], queryFn: modelsService.list })
}
