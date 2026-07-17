import * as AvatarPrimitive from '@radix-ui/react-avatar'
import { cn } from '@/lib/utils'
import { initials } from '@/lib/utils'

export interface AvatarProps {
  src?: string
  name: string
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
  ring?: boolean
}

const sizes = { sm: 'h-8 w-8 text-xs', md: 'h-10 w-10 text-sm', lg: 'h-14 w-14 text-lg', xl: 'h-20 w-20 text-2xl' }

export function Avatar({ src, name, size = 'md', className, ring = false }: AvatarProps) {
  return (
    <AvatarPrimitive.Root
      className={cn(
        'relative inline-flex shrink-0 select-none items-center justify-center overflow-hidden rounded-full bg-gradient-brand font-semibold text-white',
        sizes[size],
        ring && 'ring-2 ring-white dark:ring-surface-dark',
        className
      )}
    >
      <AvatarPrimitive.Image src={src} alt={name} className="h-full w-full object-cover" />
      <AvatarPrimitive.Fallback delayMs={src ? 300 : 0}>{initials(name) || '?'}</AvatarPrimitive.Fallback>
    </AvatarPrimitive.Root>
  )
}
