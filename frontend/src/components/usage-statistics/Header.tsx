
import type React from "react"

interface HeaderProps {
  onRefresh: () => void
  isLoading: boolean
}

const Header: React.FC<HeaderProps> = ({ onRefresh, isLoading }) => {
  return (
    <div className="flex items-center justify-between mb-6">
      <h2 className="text-lg font-semibold text-[var(--color-primary)]">Usage Statistics</h2>
      <button onClick={onRefresh} className="text-xs btn btn-ghost" disabled={isLoading}>
        {isLoading ? "Refreshing..." : "Refresh"}
      </button>
    </div>
  )
}

export default Header
