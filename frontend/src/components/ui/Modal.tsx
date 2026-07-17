import * as React from 'react'
import * as DialogPrimitive from '@radix-ui/react-dialog'
import { AnimatePresence, motion } from 'framer-motion'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface ModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title?: React.ReactNode
  description?: React.ReactNode
  children?: React.ReactNode
  className?: string
  hideClose?: boolean
}

export function Modal({ open, onOpenChange, title, description, children, className, hideClose }: ModalProps) {
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
                  'fixed left-1/2 top-1/2 z-50 w-[92vw] max-w-md -translate-x-1/2 -translate-y-1/2',
                  'card-surface p-6 focus:outline-none',
                  className
                )}
                initial={{ opacity: 0, scale: 0.95, y: 8 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.96, y: 4 }}
                transition={{ duration: 0.2, ease: 'easeOut' }}
              >
                {(title || !hideClose) && (
                  <div className="mb-4 flex items-start justify-between gap-4">
                    <div>
                      {title && (
                        <DialogPrimitive.Title className="text-lg font-semibold text-slate-900 dark:text-white">
                          {title}
                        </DialogPrimitive.Title>
                      )}
                      {description && (
                        <DialogPrimitive.Description className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                          {description}
                        </DialogPrimitive.Description>
                      )}
                    </div>
                    {!hideClose && (
                      <DialogPrimitive.Close className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-white/[0.06] dark:hover:text-slate-200">
                        <X className="h-4 w-4" />
                      </DialogPrimitive.Close>
                    )}
                  </div>
                )}
                {children}
              </motion.div>
            </DialogPrimitive.Content>
          </DialogPrimitive.Portal>
        )}
      </AnimatePresence>
    </DialogPrimitive.Root>
  )
}
