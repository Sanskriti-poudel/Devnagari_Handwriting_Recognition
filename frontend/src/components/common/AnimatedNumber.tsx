import { useCountUp } from '@/hooks/useCountUp'

export interface AnimatedNumberProps {
  value: number
  decimals?: number
  suffix?: string
  prefix?: string
  className?: string
}

export function AnimatedNumber({ value, decimals = 0, suffix = '', prefix = '', className }: AnimatedNumberProps) {
  const { ref, value: animated } = useCountUp(value)
  return (
    <span ref={ref as React.RefObject<HTMLSpanElement>} className={className}>
      {prefix}
      {animated.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}
      {suffix}
    </span>
  )
}
