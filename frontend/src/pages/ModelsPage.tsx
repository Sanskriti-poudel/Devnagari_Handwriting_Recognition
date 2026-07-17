import { Cpu, Layers } from 'lucide-react'
import { Breadcrumb } from '@/components/ui/Breadcrumb'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { SkeletonCard } from '@/components/ui/Skeleton'
import { PageTransition, staggerContainer, staggerItem } from '@/components/common/PageTransition'
import { motion } from 'framer-motion'
import { useModels } from '@/hooks/useModels'

const ICONS = { crnn: Cpu, transformer: Layers }

export default function ModelsPage() {
  const { data: models, isLoading } = useModels()

  return (
    <PageTransition>
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <Breadcrumb items={[{ label: 'Models' }]} />
          <h1 className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">Recognition Models</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            The models available for handwritten Devanagari recognition.
          </p>
        </div>

        <motion.div variants={staggerContainer} initial="hidden" animate="show" className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {isLoading || !models
            ? Array.from({ length: 2 }).map((_, i) => <SkeletonCard key={i} />)
            : models.map((model) => {
                const Icon = ICONS[model.id]
                return (
                  <Card key={model.id} hover variants={staggerItem}>
                    <CardHeader>
                      <div className="flex items-center gap-3">
                        <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-brand-soft text-violet-600 dark:text-violet-400">
                          <Icon className="h-5 w-5" />
                        </span>
                        <div>
                          <CardTitle>{model.name}</CardTitle>
                        </div>
                      </div>
                      <Badge variant={model.status === 'active' ? 'emerald' : 'outline'} dot>
                        {model.status}
                      </Badge>
                    </CardHeader>
                    <CardDescription>{model.description}</CardDescription>
                  </Card>
                )
              })}
        </motion.div>
      </div>
    </PageTransition>
  )
}
