import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { motion, useAnimation } from 'framer-motion'
import { CheckCircle2, Mail, User } from 'lucide-react'
import { Input } from '@/components/ui/Input'
import { PasswordInput } from '@/features/auth/PasswordInput'
import { FormField } from '@/components/ui/FormField'
import { Button } from '@/components/ui/Button'
import { SocialButtons } from '@/features/auth/SocialButtons'
import { useAuthStore } from '@/stores/auth.store'
import { toast } from '@/components/ui/Toast'

const schema = z
  .object({
    fullName: z.string().min(2, 'Enter your full name'),
    email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
    password: z.string().min(8, 'Must be at least 8 characters'),
    confirmPassword: z.string().min(1, 'Confirm your password'),
    terms: z.boolean().refine((v) => v === true, { message: 'You must accept the terms to continue' }),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

type FormValues = z.infer<typeof schema>

export function SignupForm() {
  const navigate = useNavigate()
  const signup = useAuthStore((s) => s.signup)
  const [success, setSuccess] = useState(false)
  const controls = useAnimation()

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const onSubmit = async (values: FormValues) => {
    try {
      await signup(values)
      setSuccess(true)
      toast.success('Account created!', 'Welcome to Devanagari OCR.')
      setTimeout(() => navigate('/dashboard', { replace: true }), 500)
    } catch (err) {
      toast.error('Sign up failed', (err as Error).message)
      controls.start({ x: [0, -8, 8, -6, 6, 0], transition: { duration: 0.4 } })
    }
  }

  return (
    <motion.div animate={controls}>
      <div className="mb-7 text-center">
        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Create your account</h1>
        <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">Sign up to get started</p>
      </div>

      <SocialButtons />

      <div className="my-6 flex items-center gap-3 text-xs font-medium text-slate-400">
        <span className="h-px flex-1 bg-slate-200 dark:bg-white/10" />
        or
        <span className="h-px flex-1 bg-slate-200 dark:bg-white/10" />
      </div>

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
        <FormField label="Full Name" htmlFor="fullName" error={errors.fullName?.message}>
          <Input
            id="fullName"
            autoComplete="name"
            placeholder="Savyata Poudel"
            icon={<User className="h-4 w-4" />}
            error={!!errors.fullName}
            {...register('fullName')}
          />
        </FormField>

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

        <FormField label="Password" htmlFor="password" error={errors.password?.message}>
          <PasswordInput
            id="password"
            autoComplete="new-password"
            placeholder="••••••••"
            error={!!errors.password}
            {...register('password')}
          />
        </FormField>

        <FormField label="Confirm Password" htmlFor="confirmPassword" error={errors.confirmPassword?.message}>
          <PasswordInput
            id="confirmPassword"
            autoComplete="new-password"
            placeholder="••••••••"
            error={!!errors.confirmPassword}
            {...register('confirmPassword')}
          />
        </FormField>

        <div>
          <label className="flex select-none items-start gap-2 text-sm text-slate-600 dark:text-slate-300">
            <input
              type="checkbox"
              className="mt-0.5 h-4 w-4 rounded border-slate-300 text-violet-600 focus:ring-violet-500 dark:border-white/20 dark:bg-white/[0.04]"
              {...register('terms')}
            />
            I agree to the Terms of Service &amp; Privacy Policy
          </label>
          {errors.terms && <p className="mt-1 text-xs font-medium text-rose-500">{errors.terms.message}</p>}
        </div>

        <Button type="submit" className="w-full" loading={isSubmitting} disabled={success}>
          {success ? (
            <motion.span initial={{ scale: 0 }} animate={{ scale: 1 }} className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4" /> Account created
            </motion.span>
          ) : (
            'Sign Up'
          )}
        </Button>

        <p className="text-center text-sm text-slate-500 dark:text-slate-400">
          Already have an account?{' '}
          <Link to="/login" className="font-semibold text-violet-600 hover:underline dark:text-violet-400">
            Sign in
          </Link>
        </p>
      </form>
    </motion.div>
  )
}
