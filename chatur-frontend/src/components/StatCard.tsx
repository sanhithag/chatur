interface Props {
  icon: React.ReactNode
  label: string
  value: number | string
  bg?: string
}

export default function StatCard({ icon, label, value, bg = 'bg-slate-50' }: Props) {
  return (
    <div className={`card p-4 ${bg}`}>
      <div className="flex items-center gap-2 mb-2">{icon}</div>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      <div className="text-xs text-slate-500 mt-0.5">{label}</div>
    </div>
  )
}
