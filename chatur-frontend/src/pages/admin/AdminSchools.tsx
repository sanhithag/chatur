import { useQuery } from '@tanstack/react-query'
import { useI18n } from '@/i18n/I18nProvider'
import PageHeader from '@/components/PageHeader'
import LoadingSpinner from '@/components/LoadingSpinner'
import ErrorMessage from '@/components/ErrorMessage'
import api from '@/lib/api'

export default function AdminSchools() {
  const { t } = useI18n()

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-schools'],
    queryFn: async () => {
      const res = await api.get('/admin/schools')
      return res.data
    },
  })

  if (isLoading) return <LoadingSpinner />
  if (isError) return <ErrorMessage onRetry={refetch} />

  const schools: any[] = data?.items ?? []

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <PageHeader title={t('nav_schools')} subtitle={`${schools.length} schools registered`} />
      <div className="grid gap-4">
        {schools.map((s: any) => (
          <div key={s.id} className="card">
            <div className="card-header flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-slate-900">{s.name}</h3>
                <p className="text-xs text-slate-500 mt-0.5">{s.district}, {s.state} · {s.board}</p>
              </div>
              <span className={`badge ${s.is_active ? 'badge-green' : 'badge-red'}`}>
                {s.is_active ? t('active') : t('inactive')}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
