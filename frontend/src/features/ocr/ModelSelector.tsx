import { Cpu, Layers } from 'lucide-react'
import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'
import type { OcrModel, OcrModelId } from '@/types'

const ICONS: Record<OcrModelId, typeof Cpu> = { crnn: Cpu, transformer: Layers }

export interface ModelSelectorProps {
  models: OcrModel[]
  value: OcrModelId
  onChange: (value: OcrModelId) => void
  disabled?: boolean
}

export function ModelSelector({ models, value, onChange, disabled }: ModelSelectorProps) {
  return (
    <fieldset className="space-y-2.5" disabled={disabled}>
      <legend className="mb-1 text-sm font-semibold text-slate-700 dark:text-slate-300">Select Model</legend>
      {models.map((model) => {
        const Icon = ICONS[model.id]
        const selected = value === model.id
        return (
          <label
            key={model.id}
            className={cn(
              'relative flex cursor-pointer items-center gap-3 rounded-xl border p-3.5 transition-all duration-200',
              selected
                ? 'border-violet-500 bg-violet-50/60 shadow-glow dark:bg-violet-500/10'
                : 'border-slate-200 hover:border-violet-300 dark:border-white/10 dark:hover:border-violet-500/30',
              disabled && 'pointer-events-none opacity-60'
            )}
          >
            <input
              type="radio"
              name="ocr-model"
              value={model.id}
              checked={selected}
              onChange={() => onChange(model.id)}
              className="sr-only"
            />
            <span
              className={cn(
                'flex h-9 w-9 shrink-0 items-center justify-center rounded-lg',
                selected ? 'bg-gradient-brand text-white' : 'bg-slate-100 text-slate-500 dark:bg-white/[0.06]'
              )}
            >
              <Icon className="h-4 w-4" />
            </span>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{model.name}</p>
              <p className="truncate text-xs text-slate-400">{model.description}</p>
            </div>
            <span
              className={cn(
                'flex h-[18px] w-[18px] shrink-0 items-center justify-center rounded-full border-2 transition-colors',
                selected ? 'border-violet-500' : 'border-slate-300 dark:border-white/20'
              )}
            >
              {selected && (
                <motion.span
                  layoutId="model-radio-dot"
                  className="h-2 w-2 rounded-full bg-violet-500"
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              )}
            </span>
          </label>
        )
      })}
    </fieldset>
  )
}
