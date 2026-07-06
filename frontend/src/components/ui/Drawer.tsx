import * as React from 'react'
import * as DialogPrimitive from '@radix-ui/react-dialog'
import { AnimatePresence, motion } from 'framer-motion'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface DrawerProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title?: React.ReactNode
  side?: 'left' | 'right'
  children?: React.ReactNode
  className?: string
}

export function Drawer({ open, onOpenChange, title, side = 'left', children, className }: DrawerProps) {
  return (
    <DialogPrimitive.Root open={open} onOpenChange={onOpenChange}>
      <AnimatePresence>
        {open && (
          <DialogPrimitive.Portal forceMount>
            <DialogPrimitive.Overlay asChild forceMount>
              <motion.div
                className="fixed inset-0 z-50 bg-slate-950/50 backdrop-blur-sm"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              />
            </DialogPrimitive.Overlay>
            <DialogPrimitive.Content asChild forceMount>
              <motion.div
                className={cn(
                  'fixed top-0 z-50 h-full w-[85vw] max-w-xs glass glass-border p-5',
                  side === 'left' ? 'left-0 border-r' : 'right-0 border-l',
                  className
                )}
                initial={{ x: side === 'left' ? '-100%' : '100%' }}
                animate={{ x: 0 }}
                exit={{ x: side === 'left' ? '-100%' : '100%' }}
                transition={{ type: 'spring', stiffness: 320, damping: 34 }}
              >
                <div className="mb-4 flex items-center justify-between">
                  {title && (
                    <DialogPrimitive.Title className="text-base font-semibold text-slate-900 dark:text-white">
                      {title}
                    </DialogPrimitive.Title>
                  )}
                  <DialogPrimitive.Close className="ml-auto rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/[0.06] dark:hover:text-slate-200">
                    <X className="h-4 w-4" />
                  </DialogPrimitive.Close>
                </div>
                {children}
              </motion.div>
            </DialogPrimitive.Content>
          </DialogPrimitive.Portal>
        )}
      </AnimatePresence>
    </DialogPrimitive.Root>
  )
}
