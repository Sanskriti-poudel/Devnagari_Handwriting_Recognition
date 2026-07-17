import type { ReactNode } from 'react'

export function SettingsRow({ label, description, children }: { label: string; description?: string; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 py-3.5 first:pt-0 last:pb-0">
      <div className="min-w-0">
        <p className="text-sm font-medium text-slate-800 dark:text-slate-100">{label}</p>
        {description && <p className="mt-0.5 text-xs text-slate-400">{description}</p>}
      </div>
      <div className="shrink-0">{children}</div>
    </div>
  )
}
