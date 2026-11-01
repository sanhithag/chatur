import { AlertCircle, RefreshCw } from 'lucide-react'

export default function ErrorMessage({ message, onRetry }: { message?: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[200px] gap-3 p-8">
      <AlertCircle className="w-8 h-8 text-red-500" />
      <p className="text-sm text-slate-600">{message ?? 'Something went wrong. Please try again.'}</p>
      {onRetry && (
        <button onClick={onRetry} className="btn-secondary text-xs gap-1.5">
          <RefreshCw className="w-3.5 h-3.5" /> Retry
        </button>
      )}
    </div>
  )
}
