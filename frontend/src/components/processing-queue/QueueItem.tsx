import type React from "react"
import { File, Eye, X } from "lucide-react"
import type { QueueItemProps } from "../../types/processginQueueTypes"
import StatusIcon from "./StatusIcon"

const QueueItem: React.FC<QueueItemProps> = ({ document, onViewDocument, onCancelDocument }) => {
  const getStatusBadgeStyles = (status: string) => ({
    backgroundColor:
      status === "Completed"
        ? "#dcfce7"
        : status === "Processing"
          ? "#dbeafe"
          : status === "Failed"
            ? "#fee2e2"
            : "#f3f4f6",
    color:
      status === "Completed"
        ? "#166534"
        : status === "Processing"
          ? "#1e40af"
          : status === "Failed"
            ? "#dc2626"
            : "#6b7280",
  })

  return (
    <div
      className="transition-all duration-300 border rounded-xl hover:shadow-lg animate-slide-up group"
      style={{
        borderColor: "#E5E7EB",
        backgroundColor: "#ffffff",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.backgroundColor = "var(--bg-soft)"
        e.currentTarget.style.transform = "translateY(-2px)"
        e.currentTarget.style.borderColor = "var(--color-accent)"
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.backgroundColor = "#ffffff"
        e.currentTarget.style.transform = "translateY(0)"
        e.currentTarget.style.borderColor = "#E5E7EB"
      }}
    >
      {/* Mobile Layout */}
      <div className="block p-4 space-y-3 md:hidden">
        {/* Document info row */}
        <div className="flex items-start justify-between">
          <div className="flex items-center flex-1 min-w-0 mr-3">
            <div className="flex-shrink-0 p-2 mr-3 rounded-lg" style={{ backgroundColor: "var(--bg-soft)" }}>
              <File className="w-4 h-4" style={{ color: "var(--color-accent)" }} />
            </div>
            <div className="flex-1 min-w-0">
              <p
                className="text-sm font-semibold truncate"
                style={{ color: "var(--color-primary)" }}
                title={document.name}
              >
                {document.name}
              </p>
              {document.file_type && (
                <p className="mt-1 text-xs tracking-wide uppercase" style={{ color: "var(--color-secondary)" }}>
                  {document.file_type}
                </p>
              )}
            </div>
          </div>

          {/* Status badge */}
          <div className="flex items-center gap-1.5 flex-shrink-0">
            <StatusIcon status={document.status} />
            <span className="px-2 py-1 text-xs font-medium rounded-full" style={getStatusBadgeStyles(document.status)}>
              {document.status}
            </span>
          </div>
        </div>

        {/* Actions row */}
        <div className="flex items-center justify-between pt-2 border-t" style={{ borderColor: "#f3f4f6" }}>
          <button
            onClick={() => onViewDocument(document.id)}
            className="flex items-center gap-2 px-3 py-2 text-sm font-medium transition-all duration-200 rounded-lg"
            style={{
              color: "var(--color-accent)",
              backgroundColor: "transparent",
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = "var(--bg-soft)"
              e.currentTarget.style.color = "var(--color-primary)"
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = "transparent"
              e.currentTarget.style.color = "var(--color-accent)"
            }}
          >
            <Eye className="w-4 h-4" />
            View Document
          </button>

          {document.status !== "Completed" && (
            <button
              onClick={() => onCancelDocument(document.id)}
              className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-red-600 transition-all duration-200 rounded-lg hover:bg-red-50"
              aria-label={`Cancel processing for ${document.name}`}
              title="Remove Document"
            >
              <X className="w-4 h-4" />
              Remove
            </button>
          )}
        </div>
      </div>

      {/* Desktop Layout */}
      <div className="items-center hidden grid-cols-12 gap-4 px-4 py-4 md:grid">
        {/* Document name */}
        <div className="flex items-center min-w-0 col-span-6">
          <div className="flex-shrink-0 p-2 mr-3 rounded-lg" style={{ backgroundColor: "var(--bg-soft)" }}>
            <File className="w-4 h-4" style={{ color: "var(--color-accent)" }} />
          </div>
          <div className="flex-1 min-w-0">
            <p
              className="text-sm font-semibold truncate"
              style={{ color: "var(--color-primary)" }}
              title={document.name}
            >
              {document.name}
            </p>
            {document.file_type && (
              <p className="mt-1 text-xs tracking-wide uppercase" style={{ color: "var(--color-secondary)" }}>
                {document.file_type}
              </p>
            )}
          </div>
        </div>

        {/* Status */}
        <div className="flex items-center justify-center col-span-2">
          <div className="flex items-center gap-1.5">
            <StatusIcon status={document.status} />
            <span className="px-2 py-1 text-xs font-medium rounded-full" style={getStatusBadgeStyles(document.status)}>
              {document.status}
            </span>
          </div>
        </div>

        {/* View Document Link */}
        <div className="flex items-center justify-center col-span-3">
          <button
            onClick={() => onViewDocument(document.id)}
            className="text-sm font-medium underline transition-all duration-200 hover:no-underline"
            style={{ color: "var(--color-accent)" }}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = "var(--color-primary)"
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = "var(--color-accent)"
            }}
          >
            View Document
          </button>
        </div>

        {/* Actions */}
        <div className="flex justify-center col-span-1">
          {document.status === "Completed" ? (
            <button
              onClick={() => onViewDocument(document.id)}
              className="px-3 text-xs transition-opacity duration-200 opacity-0 btn btn-outline-accent h-9 group-hover:opacity-100 animate-pop"
              aria-label={`View document ${document.name}`}
              title="View Document"
            >
              <Eye className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={() => onCancelDocument(document.id)}
              className="px-3 text-xs transition-opacity duration-200 opacity-0 btn btn-ghost h-9 group-hover:opacity-100 hover:text-red-600"
              aria-label={`Cancel processing for ${document.name}`}
              title="Remove Document"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

export default QueueItem
