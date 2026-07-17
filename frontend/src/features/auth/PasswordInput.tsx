import * as React from 'react'
import { Eye, EyeOff, Lock } from 'lucide-react'
import { Input, type InputProps } from '@/components/ui/Input'

export const PasswordInput = React.forwardRef<HTMLInputElement, InputProps>((props, ref) => {
  const [visible, setVisible] = React.useState(false)
  return (
    <Input
      ref={ref}
      type={visible ? 'text' : 'password'}
      icon={<Lock className="h-4 w-4" />}
      endAdornment={
        <button
          type="button"
          onClick={() => setVisible((v) => !v)}
          aria-label={visible ? 'Hide password' : 'Show password'}
          className="pointer-events-auto rounded-md p-0.5 text-slate-400 transition-colors hover:text-slate-600 dark:hover:text-slate-200"
        >
          {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      }
      {...props}
    />
  )
})
PasswordInput.displayName = 'PasswordInput'
