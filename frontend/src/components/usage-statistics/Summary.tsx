import type React from "react"
import type { StatusData } from "../../types/usagestatsTypes"

interface SummaryProps {
  totalProcessed: number
  percentageChange: number
  statusData: StatusData[]
}

const Summary: React.FC<SummaryProps> = ({ totalProcessed, percentageChange, statusData }) => {
  return (
    <div className="grid grid-cols-1 gap-6 mb-8 md:grid-cols-2">
      <div className="text-center">
        <h3 className="text-sm font-medium text-[var(--color-secondary)] mb-2">Documents (30 Days)</h3>
        <div className="flex items-center justify-center gap-2">
          <span className="text-3xl font-bold text-[var(--color-accent)]">{totalProcessed}</span>
          {percentageChange !== 0 && (
            <span className={`text-sm font-semibold ${percentageChange > 0 ? "text-green-600" : "text-red-600"}`}>
              {percentageChange > 0 ? "+" : ""}
              {percentageChange}%
            </span>
          )}
        </div>
      </div>

      <div className="text-center">
        <h3 className="text-sm font-medium text-[var(--color-secondary)] mb-2">Total Documents</h3>
        <span className="text-3xl font-bold text-[var(--color-primary)]">
          {statusData.reduce((sum, item) => sum + item.value, 0)}
        </span>
      </div>
    </div>
  )
}

export default Summary
