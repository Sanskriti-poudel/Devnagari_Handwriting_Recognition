import { useQuery } from '@tanstack/react-query'
import { dashboardService } from '@/services/dashboard.service'
import { healthService } from '@/services/health.service'

export function useDashboardStats() {
  return useQuery({ queryKey: ['dashboard', 'stats'], queryFn: dashboardService.getStats })
}

export function useActivity() {
  return useQuery({ queryKey: ['dashboard', 'activity'], queryFn: dashboardService.getActivity })
}

export function useHealth() {
  return useQuery({ queryKey: ['health'], queryFn: healthService.getHealth, refetchInterval: 60_000 })
}
