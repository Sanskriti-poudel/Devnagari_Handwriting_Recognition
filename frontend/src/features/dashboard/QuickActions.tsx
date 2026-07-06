import { Link } from 'react-router-dom'
import { History, ScanText, Settings, UploadCloud } from 'lucide-react'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'

const ACTIONS = [
  { icon: UploadCloud, label: 'New Upload', to: '/ocr', tone: 'bg-indigo-50 text-indigo-600 dark:bg-indigo-500/10 dark:text-indigo-400' },
  { icon: ScanText, label: 'Recognize', to: '/ocr', tone: 'bg-violet-50 text-violet-600 dark:bg-violet-500/10 dark:text-violet-400' },
  { icon: History, label: 'View History', to: '/history', tone: 'bg-cyan-50 text-cyan-600 dark:bg-cyan-500/10 dark:text-cyan-400' },
  { icon: Settings, label: 'Settings', to: '/settings', tone: 'bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400' },
]

export function QuickActions() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {ACTIONS.map((action) => (
          <Link
            key={action.label}
            to={action.to}
            className="group flex flex-col items-center gap-2 rounded-xl border border-slate-200 p-4 text-center transition-all duration-200 hover:-translate-y-1 hover:border-violet-300 hover:shadow-glow dark:border-white/10 dark:hover:border-violet-500/30"
          >
            <span className={`flex h-10 w-10 items-center justify-center rounded-xl transition-transform duration-200 group-hover:scale-110 ${action.tone}`}>
              <action.icon className="h-5 w-5" />
            </span>
            <span className="text-xs font-medium text-slate-600 dark:text-slate-300">{action.label}</span>
          </Link>
        ))}
      </div>
    </Card>
  )
}
