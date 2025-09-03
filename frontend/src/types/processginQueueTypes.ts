export type DocumentStatus = "Uploaded" | "Processing" | "Completed" | "Failed"

export type QueueDocument = {
  id: string
  name: string
  status: DocumentStatus
  uploadedAt?: string
  file_type?: string
}

export interface ProcessingQueueProps {
  onDocumentUpdate?: () => void
}

export interface QueueHeaderProps {
  isLoading: boolean
  onRefresh: () => void
}

export interface QueueListProps {
  documents: QueueDocument[]
  onViewDocument: (documentId: string) => void
  onCancelDocument: (documentId: string) => void
}

export interface QueueItemProps {
  document: QueueDocument
  onViewDocument: (documentId: string) => void
  onCancelDocument: (documentId: string) => void
}

export interface QueueSummaryProps {
  documents: QueueDocument[]
}

export interface StatusIconProps {
  status: DocumentStatus
}
