import { PageTransition } from '@/components/common/PageTransition'
import { ForgotPasswordForm } from '@/features/auth/ForgotPasswordForm'

export default function ForgotPasswordPage() {
  return (
    <PageTransition>
      <ForgotPasswordForm />
    </PageTransition>
  )
}
