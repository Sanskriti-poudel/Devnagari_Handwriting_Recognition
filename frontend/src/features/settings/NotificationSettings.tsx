import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Switch } from '@/components/ui/Switch'
import { SettingsRow } from '@/features/settings/SettingsRow'
import { useSettingsStore } from '@/stores/settings.store'

export function NotificationSettings() {
  const { notifications, updateNotifications } = useSettingsStore()

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Notification Preferences</CardTitle>
          <CardDescription>Choose what you want to be notified about</CardDescription>
        </div>
      </CardHeader>
      <div className="divide-y divide-slate-100 dark:divide-white/[0.06]">
        <SettingsRow label="Email notifications" description="Receive updates via email">
          <Switch checked={notifications.email} onCheckedChange={(v) => updateNotifications({ email: v })} />
        </SettingsRow>
        <SettingsRow label="Push notifications" description="Browser push notifications">
          <Switch checked={notifications.push} onCheckedChange={(v) => updateNotifications({ push: v })} />
        </SettingsRow>
        <SettingsRow label="OCR complete alerts" description="Notify me when a recognition finishes">
          <Switch checked={notifications.ocrComplete} onCheckedChange={(v) => updateNotifications({ ocrComplete: v })} />
        </SettingsRow>
        <SettingsRow label="Weekly summary" description="A weekly digest of your recognition activity">
          <Switch checked={notifications.weeklySummary} onCheckedChange={(v) => updateNotifications({ weeklySummary: v })} />
        </SettingsRow>
      </div>
    </Card>
  )
}
