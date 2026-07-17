import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Switch } from '@/components/ui/Switch'
import { SettingsRow } from '@/features/settings/SettingsRow'
import { useSettingsStore } from '@/stores/settings.store'

export function PrivacySettings() {
  const { privacy, updatePrivacy } = useSettingsStore()

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Privacy</CardTitle>
          <CardDescription>Control what data is stored and shared</CardDescription>
        </div>
      </CardHeader>
      <div className="divide-y divide-slate-100 dark:divide-white/[0.06]">
        <SettingsRow label="Store recognition history" description="Keep recognized documents in your history">
          <Switch checked={privacy.storeHistory} onCheckedChange={(v) => updatePrivacy({ storeHistory: v })} />
        </SettingsRow>
        <SettingsRow label="Share anonymous analytics" description="Help us improve recognition accuracy">
          <Switch checked={privacy.shareAnalytics} onCheckedChange={(v) => updatePrivacy({ shareAnalytics: v })} />
        </SettingsRow>
      </div>
    </Card>
  )
}
