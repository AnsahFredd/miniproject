"use client"

import type React from "react"
import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ChevronDown, ChevronUp, Loader2, CheckCircle, XCircle, Clock } from "lucide-react"
import type { DocumentData, ProcessingStatus } from "../../types/documentTypes"
import { truncateText, needsTruncation } from "../../utils/formatting"

interface DocumentCardProps {
  documentData: DocumentData | null
  processingStatus: ProcessingStatus | null
  documentContent: string
  isProcessing: boolean
}

export const DocumentCard: React.FC<DocumentCardProps> = ({
  documentData,
  processingStatus,
  documentContent,
  isProcessing,
}) => {
  const [isDocumentExpanded, setIsDocumentExpanded] = useState(false)

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

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-card rounded-xl shadow-sm border overflow-hidden"
    >
      <div className="p-4 sm:p-6 border-b">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-semibold text-foreground">
            Document Review
            {documentData?.filename && (
              <span className="text-sm text-muted-foreground font-normal ml-2">({documentData.filename})</span>
            )}
          </h2>
          <motion.div className="flex items-center gap-2">
            {getProcessingStatusIcon()}
            <span
              className={`px-2 py-1 text-xs rounded ${
                documentData?.processing_status === "completed"
                  ? "bg-green-100 text-green-800"
                  : documentData?.processing_status === "processing"
                    ? "bg-blue-100 text-blue-800"
                    : documentData?.processing_status === "failed"
                      ? "bg-red-100 text-red-800"
                      : "bg-yellow-100 text-yellow-800"
              }`}
            >
              {documentData?.processing_status || "unknown"}
            </span>
          </motion.div>
        </div>
        <div className="mt-2 h-1.5 w-16 bg-gradient-to-r from-primary to-transparent rounded-full" />
        <p className="text-sm text-muted-foreground mt-3">
          {isProcessing
            ? "Document uploaded successfully. AI analysis will populate additional details below."
            : "Review the processed document, analyze clauses, and access summaries."}
        </p>
      </div>

      <motion.div className="p-4 sm:p-6" transition={{ duration: 0.4 }}>
        <motion.div
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.05 }}
          className="w-full border rounded-lg bg-muted/50"
        >
          <div className="p-4 sm:p-6">
            <div className="text-sm text-muted-foreground leading-relaxed whitespace-pre-wrap">
              <AnimatePresence mode="wait">
                {isDocumentExpanded ? (
                  <motion.div
                    key="expanded"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="max-h-96 overflow-y-auto pr-2"
                  >
                    {documentContent || "Document content loading..."}
                  </motion.div>
                ) : (
                  <motion.div
                    key="collapsed"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    {documentContent ? truncateText(documentContent, 150) : "Document content loading..."}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {documentContent && needsTruncation(documentContent, 150) && (
              <motion.button
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
                onClick={() => setIsDocumentExpanded(!isDocumentExpanded)}
                className="mt-4 flex items-center gap-2 text-[#0FA596] hover:text-[#088e81] transition-colors text-sm font-medium"
              >
                {isDocumentExpanded ? (
                  <>
                    <ChevronUp className="w-4 h-4" />
                    Show Less
                  </>
                ) : (
                  <>
                    <ChevronDown className="w-4 h-4" />
                    Show More ({Math.ceil(documentContent.length / 1000)}k chars)
                  </>
                )}
              </motion.button>
            )}
          </div>
        </motion.div>
      </motion.div>
    </motion.div>
  )
}
