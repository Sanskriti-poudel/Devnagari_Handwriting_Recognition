import { PageTransition } from '@/components/common/PageTransition'
import { ResetPasswordForm } from '@/features/auth/ResetPasswordForm'

export default function ResetPasswordPage() {
  return (
    <PageTransition>
      <ResetPasswordForm />
    </PageTransition>
  )
}
