import { FileStack, Gauge, ScanText, Type } from 'lucide-react'
import { motion } from 'framer-motion'
import { PageTransition, staggerContainer } from '@/components/common/PageTransition'
import { WelcomeBanner } from '@/features/dashboard/WelcomeBanner'
import { StatCard } from '@/features/dashboard/StatCard'
import { ConfidenceChart } from '@/features/dashboard/ConfidenceChart'
import { RecentRecognitions } from '@/features/dashboard/RecentRecognitions'
import { ModelStatusCard } from '@/features/dashboard/ModelStatusCard'
import { StorageUsageCard } from '@/features/dashboard/StorageUsageCard'
import { SystemHealthCard } from '@/features/dashboard/SystemHealthCard'
import { ActivityTimeline } from '@/features/dashboard/ActivityTimeline'
import { QuickActions } from '@/features/dashboard/QuickActions'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { useDashboardStats } from '@/hooks/useDashboard'
import { useAuthStore } from '@/stores/auth.store'

export default function DashboardPage() {
  const user = useAuthStore((s) => s.user)
  const { data: stats, isLoading } = useDashboardStats()

  return (
    <PageTransition>
      <div className="mx-auto max-w-7xl space-y-6">
        <WelcomeBanner name={user?.fullName ?? 'there'} />

        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
        >
          {isLoading || !stats ? (
            Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
          ) : (
            <>
              <StatCard icon={FileStack} label="Total Documents" value={stats.totalDocuments} delta={stats.totalDocumentsDelta} tone="indigo" />
              <StatCard icon={ScanText} label="Total Recognitions" value={stats.totalRecognitions} delta={stats.totalRecognitionsDelta} tone="violet" />
              <StatCard icon={Gauge} label="Avg. Confidence" value={stats.avgConfidence} decimals={1} suffix="%" delta={stats.avgConfidenceDelta} tone="emerald" />
              <StatCard icon={Type} label="Total Characters" value={stats.totalCharacters} delta={stats.totalCharactersDelta} tone="rose" />
            </>
          )}
        </motion.div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          {stats && <ConfidenceChart data={stats.confidenceTrend} />}
          <RecentRecognitions />
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <ModelStatusCard />
          <StorageUsageCard usedBytes={stats?.storageUsedBytes ?? 0} totalBytes={stats?.storageTotalBytes ?? 1} isLoading={isLoading} />
          <SystemHealthCard />
        </div>

        <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <QuickActions />
          </div>
          <ActivityTimeline />
        </div>
      </div>
    </PageTransition>
  )
}
