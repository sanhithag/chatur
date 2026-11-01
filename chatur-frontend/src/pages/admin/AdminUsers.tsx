import { useQuery } from '@tanstack/react-query'
import { useAuthStore } from '@/store/authStore'
import { useI18n } from '@/i18n/I18nProvider'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'
import api from '@/lib/api'

export default function AdminUsers() {
  const { t } = useI18n()
  const user = useAuthStore((s) => s.user)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-users', user?.school_id],
    queryFn: async () => {
      const res = await api.get(`/admin/schools/${user?.school_id}/users?limit=100`)
      return res.data
    },
    enabled: !!user?.school_id,
  })

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorMessage onRetry={refetch} />

  const users: any[] = data?.items ?? []
  const ROLE_BADGE: Record<string, string> = {
    student: 'badge-blue',
    teacher: 'badge-green',
    parent: 'badge-amber',
    admin: 'badge-red',
    super_admin: 'badge-red',
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <PageHeader title={t('user_management')} subtitle={`${users.length} users in this school`} />

      <div className="card overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead>
            <tr className="bg-slate-50 border-b border-slate-200">
              <th className="px-4 py-3 text-left font-medium text-slate-700">Username</th>
              <th className="px-4 py-3 text-left font-medium text-slate-700">Role</th>
              <th className="px-4 py-3 text-left font-medium text-slate-700">Language</th>
              <th className="px-4 py-3 text-center font-medium text-slate-700">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {users.map((u: any) => (
              <tr key={u.id} className="hover:bg-slate-50">
                <td className="px-4 py-3 font-medium text-slate-900">{u.username}</td>
                <td className="px-4 py-3">
                  <span className={`badge ${ROLE_BADGE[u.role] ?? 'badge-slate'}`}>{u.role}</span>
                </td>
                <td className="px-4 py-3 text-slate-600 uppercase text-xs">{u.preferred_lang}</td>
                <td className="px-4 py-3 text-center">
                  <span className={`badge ${u.is_active ? 'badge-green' : 'badge-red'}`}>
                    {u.is_active ? t('active') : t('inactive')}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
