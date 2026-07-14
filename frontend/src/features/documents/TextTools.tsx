import { useState } from 'react'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { Textarea } from '@/components/ui/Textarea'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/Tabs'
import { toast } from '@/components/ui/Toast'
import { preetiToUnicode, unicodeToPreeti } from '@/lib/preeti'

type Direction = 'p2u' | 'u2p'

export function TextTools() {
  const [dir, setDir] = useState<Direction>('p2u')
  const [input, setInput] = useState('')

  const isP2U = dir === 'p2u'
  const output = input ? (isP2U ? preetiToUnicode(input) : unicodeToPreeti(input)) : ''

  const handleCopy = () => {
    navigator.clipboard.writeText(output)
    toast.success('Copied to clipboard')
  }

  const handleSwap = () => {
    setInput(output)
    setDir(isP2U ? 'u2p' : 'p2u')
  }

  return (
    <Card>
      <CardHeader className="flex-col items-start gap-1">
        <CardTitle>Nepali text tools — Preeti ↔ Unicode</CardTitle>
        <CardDescription>Convert legacy Preeti-font text to real Unicode, and back.</CardDescription>
      </CardHeader>

      <Tabs value={dir} onValueChange={(v) => setDir(v as Direction)}>
        <TabsList>
          <TabsTrigger value="p2u">Preeti → Unicode</TabsTrigger>
          <TabsTrigger value="u2p">Unicode → Preeti</TabsTrigger>
        </TabsList>
      </Tabs>

      <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label className="mb-1.5 block text-xs font-medium text-slate-500 dark:text-slate-400">
            {isP2U ? 'Preeti text (paste here)' : 'Unicode text (paste here)'}
          </label>
          <Textarea
            className={isP2U ? 'font-mono' : undefined}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            rows={4}
            placeholder={isP2U ? 'Paste Preeti-encoded text, e.g.  g]kfn' : 'नेपाली युनिकोड यहाँ पेस्ट गर्नुहोस्'}
          />
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-medium text-slate-500 dark:text-slate-400">
            {isP2U ? 'Unicode' : 'Preeti'}
          </label>
          <Textarea className={!isP2U ? 'font-mono' : undefined} value={output} readOnly rows={4} />
        </div>
      </div>

      <div className="mt-4 flex gap-2">
        <Button type="button" variant="outline" size="sm" onClick={handleCopy}>
          Copy
        </Button>
        <Button type="button" variant="outline" size="sm" onClick={handleSwap}>
          Swap as input
        </Button>
      </div>
    </Card>
  )
}
