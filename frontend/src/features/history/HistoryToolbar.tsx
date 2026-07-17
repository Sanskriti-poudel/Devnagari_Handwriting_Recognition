import { ArrowDownAZ, ArrowUpAZ, Search } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import type { HistoryFilters } from '@/types'

export interface HistoryToolbarProps {
  filters: HistoryFilters
  onChange: (patch: Partial<HistoryFilters>) => void
}

export function HistoryToolbar({ filters, onChange }: HistoryToolbarProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
      <div className="flex-1">
        <Input
          placeholder="Search by filename or text..."
          icon={<Search className="h-4 w-4" />}
          value={filters.search}
          onChange={(e) => onChange({ search: e.target.value, page: 1 })}
        />
      </div>

      <Select value={filters.model} onValueChange={(v) => onChange({ model: v as HistoryFilters['model'], page: 1 })}>
        <SelectTrigger className="w-full sm:w-40">
          <SelectValue placeholder="Model" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Models</SelectItem>
          <SelectItem value="crnn">CRNN</SelectItem>
          <SelectItem value="transformer">Transformer</SelectItem>
        </SelectContent>
      </Select>

      <Select value={filters.status} onValueChange={(v) => onChange({ status: v as HistoryFilters['status'], page: 1 })}>
        <SelectTrigger className="w-full sm:w-36">
          <SelectValue placeholder="Status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All Status</SelectItem>
          <SelectItem value="completed">Completed</SelectItem>
          <SelectItem value="failed">Failed</SelectItem>
        </SelectContent>
      </Select>

      <Select value={filters.sortBy} onValueChange={(v) => onChange({ sortBy: v as HistoryFilters['sortBy'] })}>
        <SelectTrigger className="w-full sm:w-40">
          <SelectValue placeholder="Sort by" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="date">Date</SelectItem>
          <SelectItem value="confidence">Confidence</SelectItem>
          <SelectItem value="name">Name</SelectItem>
        </SelectContent>
      </Select>

      <Button
        variant="outline"
        size="icon"
        aria-label="Toggle sort direction"
        onClick={() => onChange({ sortDir: filters.sortDir === 'asc' ? 'desc' : 'asc' })}
      >
        {filters.sortDir === 'asc' ? <ArrowUpAZ className="h-4 w-4" /> : <ArrowDownAZ className="h-4 w-4" />}
      </Button>
    </div>
  )
}
