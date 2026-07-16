import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { motion, useAnimation } from 'framer-motion'
import { Mail, CheckCircle2 } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { PasswordInput } from '@/features/auth/PasswordInput'
import { FormField } from '@/components/ui/FormField'
import { Button } from '@/components/ui/Button'
import { SocialButtons } from '@/features/auth/SocialButtons'
import { useAuthStore } from '@/stores/auth.store'
import { toast } from '@/components/ui/Toast'

const schema = z.object({
  email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
  remember: z.boolean().optional(),
})

type FormValues = z.infer<typeof schema>

export function LoginForm() {
  const navigate = useNavigate()
  const location = useLocation()
  const login = useAuthStore((s) => s.login)
  const [success, setSuccess] = useState(false)
  const controls = useAnimation()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: { remember: true } })

  const onSubmit = async (values: FormValues) => {
    try {
      await login(values)
      setSuccess(true)
      toast.success('Welcome back!', 'You have signed in successfully.')
      const from = (location.state as { from?: { pathname?: string } })?.from?.pathname ?? '/dashboard'
      setTimeout(() => navigate(from, { replace: true }), 500)
    } catch (err) {
      toast.error('Sign in failed', (err as Error).message)
      controls.start({ x: [0, -8, 8, -6, 6, 0], transition: { duration: 0.4 } })
    }
  }

  return (
    <motion.div animate={controls}>
      <div className="mb-7 text-center">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Welcome back</h1>
        <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">Sign in to your account to continue</p>
      </div>

      <SocialButtons />

      <div className="my-6 flex items-center gap-3 text-xs font-medium text-slate-400">
        <span className="h-px flex-1 bg-slate-200 dark:bg-white/10" />
        or
        <span className="h-px flex-1 bg-slate-200 dark:bg-white/10" />
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

        <FormField
          label="Password"
          htmlFor="password"
          error={errors.password?.message}
          action={
            <Link to="/forgot-password" className="text-xs font-medium text-violet-600 hover:underline dark:text-violet-400">
              Forgot password?
            </Link>
          }
        >
          <PasswordInput
            id="password"
            autoComplete="current-password"
            placeholder="••••••••"
            error={!!errors.password}
            {...register('password')}
          />
        </FormField>

        <label className="flex select-none items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-slate-300 text-violet-600 focus:ring-violet-500 dark:border-white/20 dark:bg-white/[0.04]"
            {...register('remember')}
          />
          Remember me
        </label>

        <Button type="submit" className="w-full" loading={isSubmitting} disabled={success}>
          {success ? (
            <motion.span initial={{ scale: 0 }} animate={{ scale: 1 }} className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" /> Signed in
            </motion.span>
          ) : (
            'Sign In'
          )}
        </Button>

        <p className="text-center text-sm text-slate-500 dark:text-slate-400">
          Don't have an account?{' '}
          <Link to="/signup" className="font-semibold text-violet-600 hover:underline dark:text-violet-400">
            Sign up
          </Link>
        </p>
      </form>
    </motion.div>
  )
}
