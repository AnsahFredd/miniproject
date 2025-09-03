import type React from "react"
import type { QueueListProps } from "../../types/processginQueueTypes"
import QueueItem from "./QueueItem"

const QueueList: React.FC<QueueListProps> = ({ documents, onViewDocument, onCancelDocument }) => {
  return (
    <div className="animate-fade-in">
      {/* Desktop Header - Hidden on mobile */}
      <div
        className="hidden grid-cols-12 gap-4 px-4 py-3 mb-2 text-xs font-semibold tracking-wide uppercase border-b-2 md:grid"
        style={{
          color: "var(--color-secondary)",
          borderBottomColor: "var(--color-accent)",
          background: "linear-gradient(135deg, var(--bg-soft) 0%, #ffffff 100%)",
        }}
      >
        <div className="col-span-6">Document Name</div>
        <div className="col-span-2 text-center">Status</div>
        <div className="col-span-3 text-center">View Document</div>
        <div className="col-span-1 text-center">Actions</div>
      </div>

      {/* Document rows */}
      <div className="space-y-3">
        {documents.map((doc, index) => (
          <div key={doc.id} style={{ animationDelay: `${index * 75}ms` }}>
            <QueueItem document={doc} onViewDocument={onViewDocument} onCancelDocument={onCancelDocument} />
          </div>
        ))}
      </div>
    </div>
  )
}

export default QueueList
