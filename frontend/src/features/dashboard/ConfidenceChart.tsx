import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Card, CardHeader, CardTitle } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { useThemeStore } from '@/stores/theme.store'

interface ConfidenceChartProps {
  data: { label: string; value: number }[]
}

export function ConfidenceChart({ data }: ConfidenceChartProps) {
  const isDark = useThemeStore((s) => s.resolvedTheme === 'dark')
  const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(15,23,42,0.06)'
  const textColor = isDark ? '#71717a' : '#94a3b8'

  return (
    <Card className="col-span-1 lg:col-span-2">
      <CardHeader>
        <CardTitle>Confidence Over Time</CardTitle>
        <Badge variant="outline">This Month</Badge>
      </CardHeader>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="confidenceFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#7C3AED" stopOpacity={0.35} />
                <stop offset="100%" stopColor="#7C3AED" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="confidenceStroke" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#4F46E5" />
                <stop offset="50%" stopColor="#7C3AED" />
                <stop offset="100%" stopColor="#06B6D4" />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
            <XAxis dataKey="label" tick={{ fontSize: 11, fill: textColor }} axisLine={false} tickLine={false} />
            <YAxis
              domain={[0, 100]}
              tickFormatter={(v) => `${v}%`}
              tick={{ fontSize: 11, fill: textColor }}
              axisLine={false}
              tickLine={false}
              width={44}
            />
            <Tooltip
              contentStyle={{
                borderRadius: 12,
                border: 'none',
                background: isDark ? '#18181B' : '#fff',
                boxShadow: '0 4px 24px -4px rgba(15,15,30,0.15)',
                fontSize: 12,
              }}
              formatter={(value) => [`${value}%`, 'Confidence']}
            />
            <Area
              type="monotone"
              dataKey="value"
              stroke="url(#confidenceStroke)"
              strokeWidth={2.5}
              fill="url(#confidenceFill)"
              animationDuration={900}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </Card>
  )
}
