import { motion } from 'framer-motion'
import { ScanText } from 'lucide-react'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { SkeletonText } from '@/components/ui/Skeleton'
import { EmptyState } from '@/components/common/EmptyState'
import { useActivity } from '@/hooks/useDashboard'
import { formatDateTime } from '@/lib/utils'

export function ActivityTimeline() {
  const { data: activity, isLoading } = useActivity()

  return (
    <Card>
      <CardHeader>
        <CardTitle>Activity Timeline</CardTitle>
      </CardHeader>
      {isLoading ? (
        <SkeletonText lines={4} />
      ) : !activity?.length ? (
        <EmptyState icon={<ScanText className="h-6 w-6" />} title="No activity yet" description="Your recent actions will show up here." />
      ) : (
        <ol className="relative space-y-5 border-l border-slate-200 pl-5 dark:border-white/10">
          {activity.map((item, i) => (
            <motion.li
              key={item.id}
              initial={{ opacity: 0, x: -8 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.06 }}
              className="relative"
            >
              <span className="absolute -left-[26px] top-1 h-2.5 w-2.5 rounded-full bg-gradient-brand ring-4 ring-white dark:ring-card-dark" />
              <p className="text-sm text-slate-700 dark:text-slate-200">{item.message}</p>
              <p className="text-xs text-slate-400">{formatDateTime(item.createdAt)}</p>
            </motion.li>
          ))}
        </ol>
      )}
    </Card>
  )
}
