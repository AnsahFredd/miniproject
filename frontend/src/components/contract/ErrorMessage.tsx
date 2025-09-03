
// ErrorMessage.tsx
import { AlertCircle, RefreshCw } from "lucide-react"

interface ErrorMessageProps {
  message?: string
  onRetry?: () => void
}

export function ErrorMessage({
  message = "Something went wrong while loading the news feed.",
  onRetry,
}: ErrorMessageProps) {
  return (
    <div className="text-center py-12 animate-fade-in">
      <div className="max-w-md mx-auto">
        <div className="mb-4">
          <div className="w-16 h-16 bg-red-50 border border-red-100 rounded-full flex items-center justify-center mx-auto mb-4 animate-pop">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>
        <h3 className="text-lg font-semibold mb-2" style={{ color: 'var(--color-primary)' }}>
          Error Loading News
        </h3>
        <p className="mb-6" style={{ color: 'var(--color-secondary)' }}>
          {message}
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="btn btn-primary flex items-center gap-2 mx-auto"
          >
            <RefreshCw className="h-4 w-4" />
            Try Again
          </button>
        )}
      </div>
    </div>
  )
}