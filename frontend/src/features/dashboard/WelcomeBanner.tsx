import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { ArrowRight, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { GradientBlobs } from '@/components/common/GradientBlobs'

export function WelcomeBanner({ name }: { name: string }) {
  const firstName = name.split(' ')[0]
  return (
    <motion.div
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative overflow-hidden rounded-2xl bg-gradient-brand p-6 text-white shadow-glow sm:p-8"
    >
      <GradientBlobs className="opacity-50" />
      <div className="relative z-10 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="flex items-center gap-2 text-xl font-bold sm:text-2xl">
            <motion.span
              animate={{ rotate: [0, 14, -8, 14, 0] }}
              transition={{ duration: 1.4, delay: 0.4 }}
              className="inline-block origin-[70%_70%]"
            >
              👋
            </motion.span>
            Welcome back, {firstName}
          </h1>
          <p className="mt-1.5 text-sm text-white/80">Let's recognize some handwritten magic today!</p>
        </div>
        <Button asChild variant="secondary" className="w-fit bg-white text-violet-700 hover:bg-white/90">
          <Link to="/ocr">
            <Sparkles className="h-4 w-4" /> New Recognition <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>
    </motion.div>
  )
}
