import { motion } from 'framer-motion'
import { NeuralDots } from '@/components/ui/Loader'

export function ScanningOverlay() {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-end gap-3 overflow-hidden bg-slate-950/40 pb-5 backdrop-blur-[1px]">
      <motion.div
        className="absolute inset-x-0 h-1/3 bg-gradient-to-b from-transparent via-violet-400/40 to-transparent"
        style={{ boxShadow: '0 0 24px 4px rgba(124,58,237,0.5)' }}
        initial={{ top: '-33%' }}
        animate={{ top: ['-10%', '100%'] }}
        transition={{ duration: 1.8, repeat: Infinity, ease: 'easeInOut' }}
      />
      <div className="relative z-10 flex items-center gap-2 rounded-full bg-white/90 px-4 py-2 shadow-lg dark:bg-slate-900/90">
        <NeuralDots />
        <span className="text-xs font-semibold text-slate-700 dark:text-slate-200">Recognizing handwriting…</span>
      </div>
    </div>
  )
}
