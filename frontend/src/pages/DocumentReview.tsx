"use client"

import React, { useMemo } from "react"
import { useParams } from "react-router-dom"
import { motion } from "framer-motion"
import { Loader2 } from "lucide-react"

// Hooks
import { useDocumentData } from "../hooks/useDocumetnData"
import { useProcessingStatus } from "../hooks/useProcessingStatus"

// Utils
import { extractKeyData } from "../utils/clauseUtils"

// UI Components
import { ProcessingStatusAlert } from "../components/document/ProcessingStatusAlert"
import { DocumentCard } from "../components/document/DocumentCard"
import { ClauseOverview } from "../components/document/ClauseOverview"
import { SummaryCard } from "../components/document/SummaryCard"
import { CompletionCallout } from "../components/document/CompletionCallout"

const DocumentReview = () => {
  const { id: documentId } = useParams<{ id: string }>()

  // Custom hooks for data management
  const { documentData, analysisData, loading, error, refetchDocument, refetchAnalysis } = useDocumentData(documentId)

  const { processingStatus, startPolling } = useProcessingStatus(documentId, async () => {
    // When processing completes, refetch data
    await refetchAnalysis()
    await refetchDocument()
  })

  const containerVariants = useMemo(
    () => ({
      hidden: { opacity: 0 },
      show: {
        opacity: 1,
        transition: { staggerChildren: 0.06, when: "beforeChildren" },
      },
    }),
    [],
  )

  const itemVariants = useMemo(
    () => ({
      hidden: { opacity: 0, y: 10 },
      show: { opacity: 1, y: 0 },
    }),
    [],
  )

  const keyData = extractKeyData(analysisData, documentData)
  const documentContent = documentData?.content || analysisData?.document_info?.content || ""
  const summary = documentData?.summary || analysisData?.summary?.text || ""
  const isProcessing = documentData?.processing_status === "processing" || documentData?.processing_status === "pending"

  // Start polling if document is processing
  React.useEffect(() => {
    if (isProcessing) {
      startPolling()
    }
  }, [isProcessing, startPolling])

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto p-4 sm:p-6 bg-background">
        <div className="flex items-center justify-center py-12" role="status" aria-live="polite">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto mb-4" />
            <p className="text-muted-foreground">Loading document...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error && !documentData) {
    return (
      <div className="max-w-7xl mx-auto p-4 sm:p-6 bg-background">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4" role="alert" aria-live="assertive">
          <p className="text-red-700">{error}</p>
          <button onClick={() => window.location.reload()} className="mt-2 text-primary hover:underline">
            Try again
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="relative max-w-7xl mx-auto p-4 sm:p-6 bg-background">
      {/* Decorative background accents */}
      <div className="pointer-events-none absolute -z-10 inset-0 overflow-hidden">
        <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full bg-primary/10 blur-3xl"></div>
        <div className="absolute -bottom-24 -left-24 w-96 h-96 rounded-full bg-muted/20 blur-3xl"></div>
      </div>

      {/* Processing Status Alert */}
      <ProcessingStatusAlert processingStatus={processingStatus} isProcessing={isProcessing} />

      <motion.div
        className="grid grid-cols-1 xl:grid-cols-[1fr_400px] gap-6"
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        {/* Document Review Card */}
        <motion.div variants={itemVariants}>
          <DocumentCard
            documentData={documentData}
            processingStatus={processingStatus}
            documentContent={documentContent}
            isProcessing={isProcessing}
          />
        </motion.div>

        {/* Clause Overview Card */}
        <motion.div variants={itemVariants} className="bg-card rounded-xl shadow-sm border overflow-hidden">
          <div className="p-4 sm:p-6">
            <h3 className="text-2xl font-bold text-foreground">Clause Overview</h3>
            <div className="mt-2 h-1.5 w-14 bg-gradient-to-r from-primary to-transparent rounded-full" />
          </div>

          <ClauseOverview keyData={keyData} isProcessing={isProcessing} />

          <SummaryCard summary={summary} />
        </motion.div>
      </motion.div>

      {/* Completion callout */}
      <CompletionCallout isProcessing={isProcessing} />
    </div>
  )
}

export default DocumentReview
