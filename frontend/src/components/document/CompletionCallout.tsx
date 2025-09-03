"use client"

import type React from "react"
import { motion } from "framer-motion"
import { CheckCircle } from "lucide-react"

interface CompletionCalloutProps {
  isProcessing: boolean
}

export const CompletionCallout: React.FC<CompletionCalloutProps> = ({ isProcessing }) => {
  if (isProcessing) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.25 }}
      className="mt-6 p-4 sm:p-6 bg-green-50 rounded-lg border border-green-200"
    >
      <div className="flex items-center gap-2">
        <CheckCircle className="h-5 w-5 text-green-600" />
        <span className="font-medium text-green-800">Document analysis completed</span>
      </div>
    </motion.div>
  )
}
