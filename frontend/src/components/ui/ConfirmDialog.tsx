import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'

export interface ConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  confirmLabel?: string
  destructive?: boolean
  loading?: boolean
  onConfirm: () => void
}

export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel = 'Confirm',
  destructive = true,
  loading,
  onConfirm,
}: ConfirmDialogProps) {
  return (
    <Modal open={open} onOpenChange={onOpenChange} title={title} description={description} className="max-w-sm">
      <div className="mt-2 flex justify-end gap-2.5">
        <Button variant="outline" size="sm" onClick={() => onOpenChange(false)}>
          Cancel
        </Button>
        <Button variant={destructive ? 'destructive' : 'primary'} size="sm" loading={loading} onClick={onConfirm}>
          {confirmLabel}
        </Button>
      </div>
    </Modal>
  )
}
