import { useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Camera } from 'lucide-react'
import { Card, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { Input } from '@/components/ui/Input'
import { FormField } from '@/components/ui/FormField'
import { Button } from '@/components/ui/Button'
import { Avatar } from '@/components/ui/Avatar'
import { toast } from '@/components/ui/Toast'
import { useAuthStore } from '@/stores/auth.store'
import { mockDb } from '@/services/mock/mockDb'

const schema = z.object({
  fullName: z.string().min(2, 'Enter your full name'),
  email: z.string().email(),
  university: z.string().optional(),
  role: z.string().optional(),
})

type FormValues = z.infer<typeof schema>

export function ProfileForm() {
  const user = useAuthStore((s) => s.user)
  const updateUser = useAuthStore((s) => s.updateUser)
  const fileRef = useRef<HTMLInputElement>(null)
  const [avatarUrl, setAvatarUrl] = useState(user?.avatarUrl)

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      fullName: user?.fullName ?? '',
      email: user?.email ?? '',
      university: user?.university ?? '',
      role: user?.role ?? '',
    },
  })

  const onSubmit = async (values: FormValues) => {
    if (!user) return
    const updated = mockDb.updateUser(user.id, { ...values, avatarUrl })
    updateUser(updated)
    toast.success('Profile updated')
  }

  const handleAvatarPick = (file?: File) => {
    if (!file || !user) return
    const reader = new FileReader()
    reader.onload = () => {
      const url = reader.result as string
      setAvatarUrl(url)
      const updated = mockDb.updateUser(user.id, { avatarUrl: url })
      updateUser(updated)
      toast.success('Avatar updated')
    }
    reader.readAsDataURL(file)
  }

  if (!user) return null

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Personal Information</CardTitle>
          <CardDescription>Update your photo and personal details</CardDescription>
        </div>
      </CardHeader>

      <div className="mb-6 flex items-center gap-4">
        <div className="group relative">
          <Avatar name={user.fullName} src={avatarUrl} size="xl" />
          <button
            onClick={() => fileRef.current?.click()}
            aria-label="Change avatar"
            className="absolute inset-0 flex items-center justify-center rounded-full bg-black/50 text-white opacity-0 transition-opacity group-hover:opacity-100"
          >
            <Camera className="h-5 w-5" />
          </button>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="sr-only"
            onChange={(e) => handleAvatarPick(e.target.files?.[0])}
          />
        </div>
        <div>
          <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{user.fullName}</p>
          <p className="text-xs text-slate-400">Member since {new Date(user.createdAt).toLocaleDateString()}</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <FormField label="Full Name" htmlFor="fullName" error={errors.fullName?.message}>
          <Input id="fullName" error={!!errors.fullName} {...register('fullName')} />
        </FormField>
        <FormField label="Email" htmlFor="email">
          <Input id="email" disabled {...register('email')} />
        </FormField>
        <FormField label="University" htmlFor="university">
          <Input id="university" placeholder="e.g. Tribhuvan University" {...register('university')} />
        </FormField>
        <FormField label="Role" htmlFor="role">
          <Input id="role" placeholder="e.g. Final Year Student" {...register('role')} />
        </FormField>

        <div className="sm:col-span-2">
          <Button type="submit" loading={isSubmitting} disabled={!isDirty}>
            Save Changes
          </Button>
        </div>
      </form>
    </Card>
  )
}
