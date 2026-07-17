import { PageTransition } from '@/components/common/PageTransition'
import { LoginForm } from '@/features/auth/LoginForm'

export default function LoginPage() {
  return (
    <PageTransition>
      <LoginForm />
    </PageTransition>
  )
}
