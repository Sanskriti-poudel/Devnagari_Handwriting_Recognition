import { Breadcrumb } from '@/components/ui/Breadcrumb'
import { PageTransition } from '@/components/common/PageTransition'
import { AppearanceSettings } from '@/features/settings/AppearanceSettings'
import { ApiSettings } from '@/features/settings/ApiSettings'
import { NotificationSettings } from '@/features/settings/NotificationSettings'
import { OcrDefaultsSettings } from '@/features/settings/OcrDefaultsSettings'
import { PrivacySettings } from '@/features/settings/PrivacySettings'

export default function SettingsPage() {
  return (
    <PageTransition>
      <div className="mx-auto max-w-3xl space-y-6">
        <div>
          <Breadcrumb items={[{ label: 'Settings' }]} />
          <h1 className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">Settings</h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Customize your Devanagari OCR experience.</p>
        </div>

        <AppearanceSettings />
        <ApiSettings />
        <OcrDefaultsSettings />
        <NotificationSettings />
        <PrivacySettings />
      </div>
    </PageTransition>
  )
}
