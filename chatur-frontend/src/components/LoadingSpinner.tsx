import { Loader2 } from 'lucide-react'

export default function LoadingSpinner({ message = 'Loading…' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[200px] gap-3 p-8">
      <Loader2 className="w-8 h-8 text-primary-600 animate-spin" />
      <p className="text-sm text-slate-500">{message}</p>
    </div>
  )
}
