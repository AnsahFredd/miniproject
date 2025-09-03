"use client"

import type React from "react"
import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ChevronDown, ChevronUp, Loader2 } from "lucide-react"
import { truncateText, needsTruncation } from "../../utils/formatting"

interface SummaryCardProps {
  summary: string
}

export const SummaryCard: React.FC<SummaryCardProps> = ({ summary }) => {
  const [isSummaryExpanded, setIsSummaryExpanded] = useState(false)

  if (!summary) return null

  return (
    <div className="border-t">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.1 }}
        className="p-4 sm:p-6"
      >
        <h4 className="font-semibold text-xl text-foreground mb-4">Summary</h4>
        <div className="text-sm text-muted-foreground leading-relaxed">
          <AnimatePresence mode="wait">
            {isSummaryExpanded ? (
              <motion.div
                key="summary-expanded"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="max-h-64 overflow-y-auto pr-2"
              >
                {summary}
              </motion.div>
            ) : (
              <motion.div
                key="summary-collapsed"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
              >
                {summary === "Processing..." ? (
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Generating summary...</span>
                  </div>
                ) : (
                  truncateText(summary, 120)
                )}
              </motion.div>
            )}
          </AnimatePresence>

          {summary !== "Processing..." && needsTruncation(summary, 120) && (
            <motion.button
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              onClick={() => setIsSummaryExpanded(!isSummaryExpanded)}
              className="mt-3 flex items-center gap-2 text-[#0FA596] hover:text-[rgb(9,151,137)] transition-colors text-sm font-medium"
            >
              {isSummaryExpanded ? (
                <>
                  <ChevronUp className="w-4 h-4" />
                  Show Less
                </>
              ) : (
                <>
                  <ChevronDown className="w-4 h-4" />
                  Show More
                </>
              )}
            </motion.button>
          )}
        </div>
      </motion.div>
    </div>
  )
}
