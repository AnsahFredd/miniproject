import type React from "react"
import { File, RefreshCw } from "lucide-react"
import type { QueueHeaderProps } from "../../types/processginQueueTypes"

const QueueHeader: React.FC<QueueHeaderProps> = ({ isLoading, onRefresh }) => {
  return (
    <div className="flex items-center justify-between mb-6">
      <h2
        className="flex items-center gap-2 text-lg font-semibold sm:text-xl"
        style={{ color: "var(--color-primary)" }}
      >
        <File className="w-5 h-5" style={{ color: "var(--color-accent)" }} />
        Processing Queue
      </h2>
      <button
        onClick={onRefresh}
        className="flex items-center gap-2 px-3 text-xs btn btn-ghost h-9"
        disabled={isLoading}
      >
        <RefreshCw className={`h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`} />
        <span className="hidden sm:inline">{isLoading ? "Refreshing..." : "Refresh"}</span>
      </button>
    </div>
  )
}

export default QueueHeader
