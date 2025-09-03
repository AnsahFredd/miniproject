import type React from "react"
import { useState, useEffect, useRef } from "react"
import { File } from "lucide-react"
import { useNavigate } from "react-router-dom"
import { useAuth } from "../../auth/AuthContext"
import type { ProcessingQueueProps, QueueDocument } from "../../types/processginQueueTypes"
import { fetchDocuments, cancelDocument } from "../../utils/queueUtils"
import QueueHeader from "./QueueHeader"
import QueueList from "./QueueList"
import QueueSummary from "./QueueSummary"

const ProcessingQueue: React.FC<ProcessingQueueProps> = ({ onDocumentUpdate }) => {
  const [documents, setDocuments] = useState<QueueDocument[]>([])
  const [isLoading, setIsLoading] = useState<boolean>(false)
  const [pollDelay, setPollDelay] = useState<number>(10000) // start with 10s
  const pollTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const navigate = useNavigate()
  const { token } = useAuth()

  const clearPollTimer = () => {
    if (pollTimer.current) {
      clearTimeout(pollTimer.current)
      pollTimer.current = null
    }
  }

  const handleFetchDocuments = async () => {
    if (!token) {
      console.log("No token available for fetching documents")
      return
    }

    setIsLoading(true)
    try {
      const docs = await fetchDocuments(token)
      setDocuments(docs)
      setPollDelay(10000) // Reset delay on success
    } catch (error: any) {
      if (error.response?.status === 429) {
        // Hit rate limit → backoff
        setPollDelay((prev) => Math.min(prev * 2, 300000)) // cap at 5m
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleViewDocument = (documentId: string) => {
    navigate(`/document/${documentId}/review`)
  }

  const handleCancelDocument = async (documentId: string) => {
    try {
      await cancelDocument(documentId, token!)
      setDocuments((prev) => prev.filter((doc) => doc.id !== documentId))
      onDocumentUpdate?.()
    } catch (error) {
      // Error handling is done in the utility function
    }
  }

  // Initial fetch
  useEffect(() => {
    handleFetchDocuments()
    return () => clearPollTimer()
  }, [token])

  // Adaptive polling
  useEffect(() => {
    clearPollTimer()

    const hasActiveDocs = documents.some((doc) => doc.status === "Processing" || doc.status === "Uploaded")

    if (hasActiveDocs) {
      pollTimer.current = setTimeout(() => {
        handleFetchDocuments()
        onDocumentUpdate?.()
      }, pollDelay)
    }
  }, [documents, pollDelay, onDocumentUpdate])

  return (
    <div className="max-w-4xl p-4 mx-auto mt-8 sm:p-6 card animate-slide-up">
      <QueueHeader isLoading={isLoading} onRefresh={handleFetchDocuments} />

      {isLoading ? (
        <div className="py-8 text-center animate-fade-in" role="status" aria-live="polite">
          <div
            className="w-8 h-8 mx-auto mb-4 rounded-full animate-spin"
            style={{
              border: "3px solid transparent",
              borderTopColor: "var(--color-accent)",
              borderRightColor: "var(--color-accent)",
            }}
          />
          <p className="text-base font-medium" style={{ color: "var(--color-primary)" }}>
            Loading documents...
          </p>
          <p className="mt-1 text-sm" style={{ color: "var(--color-secondary)" }}>
            Please wait while we fetch your documents
          </p>
        </div>
      ) : documents.length === 0 ? (
        <div className="py-12 text-center animate-fade-in">
          <div
            className="flex items-center justify-center w-16 h-16 mx-auto mb-4 rounded-full"
            style={{ backgroundColor: "var(--bg-soft)" }}
          >
            <File className="w-8 h-8" style={{ color: "var(--color-secondary)" }} />
          </div>
          <p className="mb-2 text-xl font-medium" style={{ color: "var(--color-primary)" }}>
            No documents uploaded yet
          </p>
          <p className="text-base" style={{ color: "var(--color-secondary)" }}>
            Upload your first document to start processing
          </p>
        </div>
      ) : (
        <>
          <QueueList
            documents={documents}
            onViewDocument={handleViewDocument}
            onCancelDocument={handleCancelDocument}
          />
          <QueueSummary documents={documents} />
        </>
      )}
    </div>
  )
}

export default ProcessingQueue
