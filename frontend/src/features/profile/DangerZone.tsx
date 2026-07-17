import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogOut, Trash2 } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Button } from '@/components/ui/Button'
import { ConfirmDialog } from '@/components/ui/ConfirmDialog'
import { toast } from '@/components/ui/Toast'
import { useAuthStore } from '@/stores/auth.store'
import { mockDb } from '@/services/mock/mockDb'

export function DangerZone() {
  const navigate = useNavigate()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const handleLogout = async () => {
    await logout()
    toast.success('Signed out')
    navigate('/login')
  }

  const handleDelete = async () => {
    if (!user) return
    setDeleting(true)
    mockDb.deleteUser(user.id)
    await logout()
    setDeleting(false)
    toast.success('Account deleted')
    navigate('/signup')
  }

  return (
    <>
      <Card className="border-rose-200 dark:border-rose-500/20">
        <CardHeader>
          <div>
            <CardTitle className="text-rose-600 dark:text-rose-400">Danger Zone</CardTitle>
            <CardDescription>Irreversible actions for your account</CardDescription>
          </div>
        </CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button variant="outline" onClick={handleLogout}>
            <LogOut className="h-4 w-4" /> Log out
          </Button>
          <Button variant="destructive" onClick={() => setConfirmOpen(true)}>
            <Trash2 className="h-4 w-4" /> Delete Account
          </Button>
        </div>
      </Card>

      <ConfirmDialog
        open={confirmOpen}
        onOpenChange={setConfirmOpen}
        title="Delete your account?"
        description="This will permanently delete your account and all recognition history. This action cannot be undone."
        confirmLabel="Delete Account"
        loading={deleting}
        onConfirm={handleDelete}
      />
    </>
  )
}
