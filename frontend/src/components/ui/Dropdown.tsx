import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu'
import { cn } from '@/lib/utils'

export const Dropdown = DropdownMenuPrimitive.Root
export const DropdownTrigger = DropdownMenuPrimitive.Trigger

export function DropdownContent({
  className,
  align = 'end',
  sideOffset = 8,
  ...props
}: React.ComponentProps<typeof DropdownMenuPrimitive.Content>) {
  return (
    <DropdownMenuPrimitive.Portal>
      <DropdownMenuPrimitive.Content
        align={align}
        sideOffset={sideOffset}
        className={cn(
          'z-50 min-w-[12rem] rounded-xl border border-slate-200 bg-white p-1.5 shadow-card',
          'data-[state=open]:animate-fade-in-up dark:border-white/10 dark:bg-card-dark dark:shadow-card-dark',
          className
        )}
        {...props}
      />
    </DropdownMenuPrimitive.Portal>
  )
}

export function DropdownItem({ className, ...props }: React.ComponentProps<typeof DropdownMenuPrimitive.Item>) {
  return (
    <DropdownMenuPrimitive.Item
      className={cn(
        'flex cursor-pointer select-none items-center gap-2.5 rounded-lg px-3 py-2 text-sm text-slate-700 outline-none transition-colors',
        'hover:bg-slate-100 focus:bg-slate-100 dark:text-slate-200 dark:hover:bg-white/[0.08] dark:focus:bg-white/[0.08]',
        'data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
        className
      )}
      {...props}
    />
  )
}

export function DropdownSeparator({ className, ...props }: React.ComponentProps<typeof DropdownMenuPrimitive.Separator>) {
  return (
    <DropdownMenuPrimitive.Separator
      className={cn('my-1 h-px bg-slate-200 dark:bg-white/10', className)}
      {...props}
    />
  )
}

export function DropdownLabel({ className, ...props }: React.ComponentProps<typeof DropdownMenuPrimitive.Label>) {
  return (
    <DropdownMenuPrimitive.Label
      className={cn('px-3 py-1.5 text-xs font-semibold uppercase tracking-wide text-slate-400', className)}
      {...props}
    />
  )
}
