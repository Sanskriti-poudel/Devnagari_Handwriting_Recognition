import { Breadcrumb } from '@/components/ui/Breadcrumb'
import { PageTransition } from '@/components/common/PageTransition'
import { ProfileForm } from '@/features/profile/ProfileForm'
import { ChangePasswordForm } from '@/features/profile/ChangePasswordForm'
import { DangerZone } from '@/features/profile/DangerZone'

export default function ProfilePage() {
  return (
    <PageTransition>
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
          <Breadcrumb items={[{ label: 'Profile' }]} />
          <h1 className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">Profile</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Manage your account information and security.</p>
        </div>

        <ProfileForm />
        <ChangePasswordForm />
        <DangerZone />
      </div>
    </PageTransition>
  )
}
