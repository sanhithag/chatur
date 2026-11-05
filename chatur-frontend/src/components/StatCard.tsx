interface Props {
  icon: React.ReactNode
  label: string
  value: number | string
  bg?: string
}

export default function StatCard({ icon, label, value, bg = 'bg-white' }: Props) {
  return (
    <div className="rounded-xl border border-[#ccd5ae] p-4 shadow-sm bg-white">
      <div className="flex items-center gap-2 mb-2 text-[#000000]">{icon}</div>
      <div className="text-2xl font-black text-[#000000]">{value}</div>
      <div className="text-xs font-bold uppercase tracking-wider text-[#333333] mt-1">{label}</div>
    </div>
  )
}
