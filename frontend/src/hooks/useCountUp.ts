import { useEffect, useRef, useState } from 'react'
import { useInView } from 'framer-motion'
import { usePrefersReducedMotion } from '@/hooks/useMediaQuery'

export function useCountUp(target: number, durationMs = 1200) {
  const ref = useRef<HTMLElement>(null)
  const isInView = useInView(ref, { once: true, margin: '-40px' })
  const reducedMotion = usePrefersReducedMotion()
  const [value, setValue] = useState(reducedMotion ? target : 0)

  useEffect(() => {
    if (!isInView) return
    if (reducedMotion) {
      setValue(target)
      return
    }
    let raf: number
    const start = performance.now()
    const tick = (now: number) => {
      const progress = Math.min((now - start) / durationMs, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      setValue(target * eased)
      if (progress < 1) raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [isInView, target, durationMs, reducedMotion])

  return { ref, value }
}
