"use client"

import type React from "react"
import { motion } from "framer-motion"
import { Loader2, CheckCircle, XCircle, Clock } from "lucide-react"
import type { ProcessingStatus } from "../../types/documentTypes"

interface ProcessingStatusAlertProps {
  processingStatus: ProcessingStatus | null
  isProcessing: boolean
}

export const ProcessingStatusAlert: React.FC<ProcessingStatusAlertProps> = ({ processingStatus, isProcessing }) => {
  const getProcessingStatusIcon = () => {
    if (!processingStatus) return null

    switch (processingStatus.processing_status) {
      case "processing":
        return <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
      case "completed":
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case "failed":
        return <XCircle className="h-5 w-5 text-red-500" />
      case "pending":
        return <Clock className="h-5 w-5 text-yellow-500" />
      default:
        return null
    }
  }

  const getProcessingMessage = () => {
    if (!processingStatus) return "Processing status unknown"

    const status = processingStatus.processing_status
    const taskInfo = processingStatus.task_info

    if (status === "completed") return "AI analysis completed"
    if (status === "failed") return `Processing failed: ${processingStatus.processing_error || "Unknown error"}`
    if (status === "pending") return "AI analysis queued"

    if (status === "processing" && taskInfo) {
      const stageMessages: { [key: string]: string } = {
        starting: "Initializing AI analysis...",
        classifying: "Analyzing document type...",
        classification_complete: "Document classification completed",
        summarizing: "Generating summary...",
        summarization_complete: "Summary completed",
        embedding: "Creating embeddings...",
        embedding_complete: "Embeddings completed",
        generating_tags: "Generating tags...",
        updating_database: "Saving results...",
        qa_integration: "Adding to knowledge base...",
      }

      return stageMessages[taskInfo.stage || ""] || taskInfo.message || "Processing..."
    }

    return "Processing..."
  }

  if (!isProcessing) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg"
    >
      <div className="flex items-center gap-3">
        {getProcessingStatusIcon()}
        <div>
          <h4 className="font-medium text-black">AI Analysis in Progress</h4>
          <p className="text-sm text-green-200 mt-1">{getProcessingMessage()}</p>
          {processingStatus?.task_info?.progress && (
            <div className="w-full bg-blue-100 rounded-full h-2 mt-2">
              <div
                className="bg-gray-200 h-2 rounded-full transition-all duration-300"
                style={{ width: `${processingStatus.task_info.progress}%` }}
              />
            </div>
          )}
          <p className="text-xs text-black mt-2">The page will automatically update when processing is complete.</p>
        </div>
      </div>
    </motion.div>
  )
}
