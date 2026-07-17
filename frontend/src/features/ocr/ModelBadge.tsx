import { Cpu, Layers } from 'lucide-react'
import { Badge } from '@/components/ui/Badge'
import type { OcrModelId } from '@/types'

export function ModelBadge({ model }: { model: OcrModelId }) {
  if (model === 'crnn') {
    return (
      <Badge variant="indigo">
        <Cpu className="h-3 w-3" /> CRNN
      </Badge>
    )
  }
  return (
    <Badge variant="cyan">
      <Layers className="h-3 w-3" /> Transformer
    </Badge>
  )
}
