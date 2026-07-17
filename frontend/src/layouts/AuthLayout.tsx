import { Outlet } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FileScan, ShieldCheck, Sparkles, Zap } from 'lucide-react'
import { GradientBlobs } from '@/components/common/GradientBlobs'
import { Logo } from '@/components/layout/Logo'

const FEATURES = [
  { icon: Sparkles, text: 'AI-powered Devanagari handwriting recognition' },
  { icon: Zap, text: 'Instant results with confidence scoring' },
  { icon: ShieldCheck, text: 'Your documents stay private and secure' },
]

export function AuthLayout() {
  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden overflow-hidden bg-slate-950 lg:flex lg:flex-col lg:justify-between lg:p-10">
        <GradientBlobs />
        <div className="relative z-10">
          <Logo onDark />
        </div>

        <div className="relative z-10 max-w-md">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-8 flex h-14 w-14 items-center justify-center rounded-2xl bg-white/10 backdrop-blur-xl"
          >
            <FileScan className="h-7 w-7 text-white" />
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-3xl font-bold leading-tight text-white"
          >
            Turn handwritten Nepali pages into editable Unicode text.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mt-4 text-sm text-white/60"
          >
            Upload a photo or PDF, choose a recognition model, and get accurate Devanagari text in seconds.
          </motion.p>
          <ul className="mt-8 space-y-4">
            {FEATURES.map((f, i) => (
              <motion.li
                key={f.text}
                initial={{ opacity: 0, x: -12 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: 0.3 + i * 0.1 }}
                className="flex items-center gap-3 text-sm text-white/80"
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-white/10">
                  <f.icon className="h-4 w-4" />
                </span>
                {f.text}
              </motion.li>
            ))}
          </ul>
        </div>

        <p className="relative z-10 text-xs text-white/40">Final year project · Devanagari Handwritten Document Recognition</p>
      </div>

      <div className="relative flex items-center justify-center bg-surface-light px-4 py-10 dark:bg-surface-dark sm:px-8">
        <div className="absolute inset-0 lg:hidden">
          <GradientBlobs className="opacity-40" />
        </div>
        <div className="relative z-10 w-full max-w-sm">
          <div className="mb-8 flex justify-center lg:hidden">
            <Logo />
          </div>
          <Outlet />
        </div>
      </div>
    </div>
  )
}
