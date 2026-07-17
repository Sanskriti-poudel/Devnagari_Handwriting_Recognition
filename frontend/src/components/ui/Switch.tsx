import * as SwitchPrimitive from '@radix-ui/react-switch'
import { cn } from '@/lib/utils'

export function Switch({ className, ...props }: React.ComponentProps<typeof SwitchPrimitive.Root>) {
  return (
    <SwitchPrimitive.Root
      className={cn(
        'relative h-6 w-11 shrink-0 rounded-full bg-slate-200 outline-none transition-colors duration-200',
        'data-[state=checked]:bg-gradient-brand dark:bg-white/10',
        className
      )}
      {...props}
    >
      <SwitchPrimitive.Thumb className="block h-5 w-5 translate-x-0.5 rounded-full bg-white shadow-sm transition-transform duration-200 will-change-transform data-[state=checked]:translate-x-[22px]" />
    </SwitchPrimitive.Root>
  )
}
