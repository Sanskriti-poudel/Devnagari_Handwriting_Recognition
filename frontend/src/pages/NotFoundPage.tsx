import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Compass } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { GradientBlobs } from '@/components/common/GradientBlobs'

export default function NotFoundPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-surface-light px-4 dark:bg-surface-dark">
      <GradientBlobs />
      <div className="relative z-10 text-center">
        <motion.div
          animate={{ y: [0, -10, 0] }}
          transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }}
          className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-brand-soft text-violet-500"
        >
          <Compass className="h-9 w-9" />
        </motion.div>
        <h1 className="text-gradient-brand text-6xl font-extrabold">404</h1>
        <p className="mt-3 text-lg font-semibold text-slate-900 dark:text-white">Page not found</p>
        <p className="mx-auto mt-2 max-w-sm text-sm text-slate-500 dark:text-slate-400">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Button asChild className="mt-6">
          <Link to="/dashboard">Back to Dashboard</Link>
        </Button>
      </div>
    </div>
  )
}
