import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/Select'
import { SettingsRow } from '@/features/settings/SettingsRow'
import { useSettingsStore } from '@/stores/settings.store'
import type { OcrModelId } from '@/types'

export function OcrDefaultsSettings() {
  const { defaultModel, downloadFormat, update } = useSettingsStore()

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>OCR Defaults</CardTitle>
          <CardDescription>Defaults applied when you start a new recognition</CardDescription>
        </div>
      </CardHeader>
      <div className="divide-y divide-slate-100 dark:divide-white/[0.06]">
        <SettingsRow label="Default model" description="Preselected on the OCR page">
          <Select value={defaultModel} onValueChange={(v) => update({ defaultModel: v as OcrModelId })}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="crnn">CRNN</SelectItem>
              <SelectItem value="transformer">Transformer</SelectItem>
            </SelectContent>
          </Select>
        </SettingsRow>
        <SettingsRow label="Download format" description="Default export format for results">
          <Select value={downloadFormat} onValueChange={(v) => update({ downloadFormat: v as 'txt' | 'pdf' })}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="txt">TXT</SelectItem>
              <SelectItem value="pdf">PDF</SelectItem>
            </SelectContent>
          </Select>
        </SettingsRow>
      </div>
    </Card>
  )
}
