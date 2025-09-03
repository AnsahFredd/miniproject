import type React from "react"

interface ErrorMessageProps {
  error: string
  onRetry: () => void
}

const ErrorMessage: React.FC<ErrorMessageProps> = ({ error, onRetry }) => {
  return (
    <div
      className="text-center py-8 text-[var(--color-primary)] text-sm bg-[var(--bg-soft)] rounded-md border border-gray-200"
      role="alert"
      aria-live="assertive"
    >
      <div className="mb-2">⚠️</div>
      <div>{error}</div>
      <button onClick={onRetry} className="mt-3 text-xs btn btn-outline-accent">
        Try Again
      </button>
    </div>
  )
}

export default ErrorMessage
