import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { motion } from 'framer-motion'
import { CheckCircle2, KeyRound } from 'lucide-react'
import { PasswordInput } from '@/features/auth/PasswordInput'
import { FormField } from '@/components/ui/FormField'
import { Button } from '@/components/ui/Button'
import { authService } from '@/services/auth.service'
import { toast } from '@/components/ui/Toast'

const schema = z
  .object({
    password: z.string().min(8, 'Must be at least 8 characters'),
    confirmPassword: z.string().min(1, 'Confirm your password'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

type FormValues = z.infer<typeof schema>

export function ResetPasswordForm() {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const [success, setSuccess] = useState(false)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const onSubmit = async (values: FormValues) => {
    try {
      await authService.resetPassword(params.get('token') ?? '', values.password)
      setSuccess(true)
      toast.success('Password reset', 'You can now sign in with your new password.')
      setTimeout(() => navigate('/login', { replace: true }), 1200)
    } catch (err) {
      toast.error('Reset failed', (err as Error).message)
    }
  }

  if (success) {
    return (
      <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} className="text-center">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 260, damping: 18 }}
          className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-500 dark:bg-emerald-500/10"
        >
          <CheckCircle2 className="h-7 w-7" />
        </motion.div>
        <h1 className="text-xl font-bold text-slate-900 dark:text-white">Password updated</h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Redirecting you to sign in…</p>
      </motion.div>
    )
  }

  return (
    <div>
      <div className="mb-7 text-center">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Reset your password</h1>
        <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">Choose a new password for your account</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        <FormField label="New Password" htmlFor="password" error={errors.password?.message}>
          <PasswordInput id="password" autoComplete="new-password" placeholder="••••••••" error={!!errors.password} {...register('password')} />
        </FormField>

        <FormField label="Confirm New Password" htmlFor="confirmPassword" error={errors.confirmPassword?.message}>
          <PasswordInput
            id="confirmPassword"
            autoComplete="new-password"
            placeholder="••••••••"
            error={!!errors.confirmPassword}
            {...register('confirmPassword')}
          />
        </FormField>

        <Button type="submit" className="w-full" loading={isSubmitting}>
          <KeyRound className="h-4 w-4" /> Reset Password
        </Button>

        <p className="text-center text-sm text-slate-500 dark:text-slate-400">
          Remembered your password?{' '}
          <Link to="/login" className="font-semibold text-violet-600 hover:underline dark:text-violet-400">
            Sign in
          </Link>
        </p>
      </form>
    </div>
  )
}
