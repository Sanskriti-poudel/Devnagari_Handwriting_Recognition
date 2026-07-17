import { Toaster as SonnerToaster, toast as sonnerToast } from 'sonner'
import { AlertTriangle, CheckCircle2, Info, XCircle } from 'lucide-react'
import { useThemeStore } from '@/stores/theme.store'

export function Toaster() {
  const resolvedTheme = useThemeStore((s) => s.resolvedTheme)
  return (
    <SonnerToaster
      theme={resolvedTheme}
      position="top-right"
      richColors
      closeButton
      toastOptions={{
        classNames: {
          toast: 'rounded-xl border shadow-card font-sans',
        },
      }}
    />
  )
}

export const toast = {
  success: (message: string, description?: string) =>
    sonnerToast.success(message, { description, icon: <CheckCircle2 className="h-4 w-4" /> }),
  error: (message: string, description?: string) =>
    sonnerToast.error(message, { description, icon: <XCircle className="h-4 w-4" /> }),
  warning: (message: string, description?: string) =>
    sonnerToast.warning(message, { description, icon: <AlertTriangle className="h-4 w-4" /> }),
  info: (message: string, description?: string) =>
    sonnerToast.info(message, { description, icon: <Info className="h-4 w-4" /> }),
}
