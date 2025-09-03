import type React from "react"
import { Clock } from "lucide-react"
import type { QueueSummaryProps } from "../../types/processginQueueTypes"

const QueueSummary: React.FC<QueueSummaryProps> = ({ documents }) => {
  const totalDocs = documents.length
  const completedDocs = documents.filter((d) => d.status === "Completed").length
  const processingDocs = documents.filter((d) => d.status === "Processing").length
  const failedDocs = documents.filter((d) => d.status === "Failed").length
  const hasActiveDocs = documents.some((d) => d.status === "Processing" || d.status === "Uploaded")

  return (
    <div
      className="p-4 pt-6 mt-8 border-t-2 rounded-lg"
      style={{
        borderTopColor: "var(--color-accent)",
        background: "linear-gradient(135deg, var(--bg-soft) 0%, #ffffff 100%)",
      }}
    >
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <div className="flex flex-wrap gap-6 sm:gap-8">
          <div className="text-center">
            <div className="text-2xl font-bold" style={{ color: "var(--color-primary)" }}>
              {totalDocs}
            </div>
            <div className="text-xs font-medium tracking-wide uppercase" style={{ color: "var(--color-secondary)" }}>
              Total
            </div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold" style={{ color: "var(--color-accent)" }}>
              {completedDocs}
            </div>
            <div className="text-xs font-medium tracking-wide uppercase" style={{ color: "var(--color-secondary)" }}>
              Completed
            </div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold" style={{ color: "var(--color-accent)" }}>
              {processingDocs}
            </div>
            <div className="text-xs font-medium tracking-wide uppercase" style={{ color: "var(--color-secondary)" }}>
              Processing
            </div>
          </div>

          {failedDocs > 0 && (
            <div className="text-center">
              <div className="text-2xl font-bold" style={{ color: "var(--color-error)" }}>
                {failedDocs}
              </div>
              <div className="text-xs font-medium tracking-wide uppercase" style={{ color: "var(--color-secondary)" }}>
                Failed
              </div>
            </div>
          )}
        </div>

        {hasActiveDocs && (
          <div
            className="flex items-center gap-2 px-3 py-2 text-sm border rounded-full"
            style={{
              color: "var(--color-secondary)",
              backgroundColor: "#ffffff",
              borderColor: "var(--color-accent)",
            }}
          >
            <Clock className="w-4 h-4 animate-pulse" />
            <span className="font-medium">Auto-refreshing every 5min</span>
          </div>
        )}
      </div>
    </div>
  )
}

export default QueueSummary
