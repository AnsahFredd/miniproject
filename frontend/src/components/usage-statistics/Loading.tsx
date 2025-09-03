import type React from "react"

const Loading: React.FC = () => {
  return (
    <div className="flex items-center justify-center h-48" role="status" aria-live="polite">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-accent)]"></div>
      <span className="ml-3 text-[var(--color-secondary)]">Loading usage data...</span>
    </div>
  )
}

export default Loading
