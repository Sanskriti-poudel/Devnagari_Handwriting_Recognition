import { PageTransition } from '@/components/common/PageTransition'
import { SignupForm } from '@/features/auth/SignupForm'

export default function SignupPage() {
  return (
    <PageTransition>
      <SignupForm />
    </PageTransition>
  )
}
