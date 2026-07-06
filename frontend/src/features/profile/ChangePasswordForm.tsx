import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { KeyRound } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { FormField } from '@/components/ui/FormField'
import { Button } from '@/components/ui/Button'
import { PasswordInput } from '@/features/auth/PasswordInput'
import { toast } from '@/components/ui/Toast'
import { useAuthStore } from '@/stores/auth.store'
import { mockDb } from '@/services/mock/mockDb'

const schema = z
  .object({
    currentPassword: z.string().min(1, 'Current password is required'),
    newPassword: z.string().min(8, 'Must be at least 8 characters'),
    confirmPassword: z.string().min(1, 'Confirm your new password'),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: 'Passwords do not match',
    path: ['confirmPassword'],
  })

type FormValues = z.infer<typeof schema>

export function ChangePasswordForm() {
  const user = useAuthStore((s) => s.user)
  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({ resolver: zodResolver(schema) })

  const onSubmit = async (values: FormValues) => {
    if (!user) return
    try {
      mockDb.changePassword(user.id, values.currentPassword, values.newPassword)
      toast.success('Password changed successfully')
      reset()
    } catch (err) {
      toast.error('Could not change password', (err as Error).message)
    }
  }

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Change Password</CardTitle>
          <CardDescription>Use a strong password you don't use elsewhere</CardDescription>
        </div>
      </CardHeader>
      <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="sm:col-span-2">
          <FormField label="Current Password" htmlFor="currentPassword" error={errors.currentPassword?.message}>
            <PasswordInput id="currentPassword" autoComplete="current-password" error={!!errors.currentPassword} {...register('currentPassword')} />
          </FormField>
        </div>
        <FormField label="New Password" htmlFor="newPassword" error={errors.newPassword?.message}>
          <PasswordInput id="newPassword" autoComplete="new-password" error={!!errors.newPassword} {...register('newPassword')} />
        </FormField>
        <FormField label="Confirm New Password" htmlFor="confirmPassword" error={errors.confirmPassword?.message}>
          <PasswordInput id="confirmPassword" autoComplete="new-password" error={!!errors.confirmPassword} {...register('confirmPassword')} />
        </FormField>
        <div className="sm:col-span-2">
          <Button type="submit" loading={isSubmitting}>
            <KeyRound className="h-4 w-4" /> Update Password
          </Button>
        </div>
      </form>
    </Card>
  )
}
