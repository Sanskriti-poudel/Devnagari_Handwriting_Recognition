import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { motion } from 'framer-motion'
import { ArrowLeft, Mail, MailCheck } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { FormField } from '@/components/ui/FormField'
import { Button } from '@/components/ui/Button'
import { authService } from '@/services/auth.service'
import { toast } from '@/components/ui/Toast'

const schema = z.object({
  email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
})

type FormValues = z.infer<typeof schema>

export function ForgotPasswordForm() {
  const [sent, setSent] = useState<string | null>(null)
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const onSubmit = async (values: FormValues) => {
    try {
      await authService.forgotPassword(values.email)
      setSent(values.email)
    } catch (err) {
      toast.error('Something went wrong', (err as Error).message)
    }
  }

  if (sent) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.96 }}
        animate={{ opacity: 1, scale: 1 }}
        className="text-center"
      >
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ type: 'spring', stiffness: 260, damping: 18 }}
          className="mx-auto mb-5 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-50 text-emerald-500 dark:bg-emerald-500/10"
        >
          <MailCheck className="h-7 w-7" />
        </motion.div>
        <h1 className="text-xl font-bold text-slate-900 dark:text-white">Check your inbox</h1>
        <p className="mx-auto mt-2 max-w-xs text-sm text-slate-500 dark:text-slate-400">
          We sent a password reset link to <span className="font-medium text-slate-700 dark:text-slate-200">{sent}</span>.
        </p>
        <Button asChild variant="outline" className="mt-6">
          <Link to="/login">
            <ArrowLeft className="h-4 w-4" /> Back to sign in
          </Link>
        </Button>
      </motion.div>
    )
  }

  return (
    <div>
      <div className="mb-7 text-center">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Forgot password?</h1>
        <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">
          Enter your email and we'll send you a reset link
        </p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        <FormField label="Email" htmlFor="email" error={errors.email?.message}>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            placeholder="you@example.com"
            icon={<Mail className="h-4 w-4" />}
            error={!!errors.email}
            {...register('email')}
          />
        </FormField>

        <Button type="submit" className="w-full" loading={isSubmitting}>
          Send Reset Link
        </Button>

        <Link
          to="/login"
          className="flex items-center justify-center gap-1.5 text-sm font-medium text-slate-500 hover:text-violet-600 dark:text-slate-400 dark:hover:text-violet-400"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back to sign in
        </Link>
      </form>
    </div>
  )
}
