import { useState } from 'react'
import { Globe, Save } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { FormField } from '@/components/ui/FormField'
import { Button } from '@/components/ui/Button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select'
import { useSettingsStore } from '@/stores/settings.store'
import { toast } from '@/components/ui/Toast'

export function ApiSettings() {
  const { apiBaseUrl, language, update } = useSettingsStore()
  const [draftUrl, setDraftUrl] = useState(apiBaseUrl)

  const handleSave = () => {
    update({ apiBaseUrl: draftUrl.replace(/\/$/, '') })
    toast.success('API base URL updated')
  }

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>API &amp; Language</CardTitle>
          <CardDescription>Configure the OCR backend endpoint and interface language</CardDescription>
        </div>
      </CardHeader>
      <div className="space-y-4">
        <FormField label="API Base URL" htmlFor="apiBaseUrl" hint="The Flask OCR backend this app talks to.">
          <div className="flex gap-2">
            <Input
              id="apiBaseUrl"
              icon={<Globe className="h-4 w-4" />}
              value={draftUrl}
              onChange={(e) => setDraftUrl(e.target.value)}
              placeholder="http://localhost:8000"
            />
            <Button variant="secondary" onClick={handleSave} disabled={draftUrl === apiBaseUrl}>
              <Save className="h-4 w-4" /> Save
            </Button>
          </div>
        </FormField>

        <FormField label="Language" htmlFor="language">
          <Select value={language} onValueChange={(v) => update({ language: v as 'en' | 'ne' })}>
            <SelectTrigger id="language" className="w-full sm:w-56">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="en">English</SelectItem>
              <SelectItem value="ne">नेपाली (Nepali)</SelectItem>
            </SelectContent>
          </Select>
        </FormField>
      </div>
    </Card>
  )
}
