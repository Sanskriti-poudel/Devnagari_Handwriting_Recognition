import * as AccordionPrimitive from '@radix-ui/react-accordion'
import { ChevronDown } from 'lucide-react'
import { cn } from '@/lib/utils'

export const Accordion = AccordionPrimitive.Root

export function AccordionItem({ className, ...props }: React.ComponentProps<typeof AccordionPrimitive.Item>) {
  return (
    <AccordionPrimitive.Item
      className={cn('border-b border-slate-200 last:border-0 dark:border-white/10', className)}
      {...props}
    />
  )
}

export function AccordionTrigger({
  className,
  children,
  ...props
}: React.ComponentProps<typeof AccordionPrimitive.Trigger>) {
  return (
    <AccordionPrimitive.Header className="flex">
      <AccordionPrimitive.Trigger
        className={cn(
          'group flex flex-1 items-center justify-between py-4 text-left text-sm font-medium text-slate-900 transition-colors hover:text-violet-600 dark:text-white dark:hover:text-violet-400',
          className
        )}
        {...props}
      >
        {children}
        <ChevronDown className="h-4 w-4 shrink-0 text-slate-400 transition-transform duration-300 group-data-[state=open]:rotate-180" />
      </AccordionPrimitive.Trigger>
    </AccordionPrimitive.Header>
  )
}

export function AccordionContent({
  className,
  children,
  ...props
}: React.ComponentProps<typeof AccordionPrimitive.Content>) {
  return (
    <AccordionPrimitive.Content
      className={cn(
        'overflow-hidden text-sm text-slate-500 dark:text-slate-400',
        'data-[state=open]:animate-fade-in-up'
      )}
      {...props}
    >
      <div className={cn('pb-4', className)}>{children}</div>
    </AccordionPrimitive.Content>
  )
}
