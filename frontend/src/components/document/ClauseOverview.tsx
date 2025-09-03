"use client"

import type React from "react"
import { motion } from "framer-motion"
import { FileText, Loader2 } from "lucide-react"
import type { ClauseItem } from "../../types/documentTypes"
import { getClauseIcon } from "../../utils/clauseUtils"

interface ClauseOverviewProps {
  keyData: ClauseItem[]
  isProcessing: boolean
}

export const ClauseOverview: React.FC<ClauseOverviewProps> = ({ keyData, isProcessing }) => {
  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: { staggerChildren: 0.06, when: "beforeChildren" },
    },
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 10 },
    show: { opacity: 1, y: 0 },
  }

  return (
    <motion.div className="px-4 sm:px-6 pb-4 space-y-3" variants={containerVariants} initial="hidden" animate="show">
      {isProcessing ? (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-8 text-muted-foreground"
        >
          <Loader2 className="w-8 h-8 mx-auto mb-2 animate-spin" />
          <p className="text-sm">Analyzing clauses...</p>
        </motion.div>
      ) : keyData.length > 0 ? (
        keyData.map((clause, index) => (
          <motion.div
            key={index}
            variants={itemVariants}
            whileHover={{ y: -2, scale: 1.01 }}
            transition={{ type: "spring", stiffness: 300, damping: 22 }}
            className="flex items-start gap-3 rounded-lg p-3 hover:bg-muted/50 border border-transparent hover:border-primary/20 transition-all duration-200"
          >
            <div className="p-2 bg-muted rounded-lg shadow-sm flex-shrink-0">
              {getClauseIcon(clause.icon || clause.type || "default")}
            </div>
            <div className="flex-1 min-w-0">
              <div className="font-medium text-foreground text-sm">{clause.title || clause.type || "Unknown"}</div>
              <div className="text-xs text-muted-foreground mt-0.5">
                {clause.subtitle || clause.category || "General"}
              </div>
              {clause.content && <div className="text-xs text-muted-foreground mt-1 opacity-75">{clause.content}</div>}
            </div>
          </motion.div>
        ))
      ) : (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-8 text-muted-foreground"
        >
          <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
          <p className="text-sm">No clauses identified</p>
          <p className="text-xs mt-1 opacity-75">Document analysis may still be in progress</p>
        </motion.div>
      )}
    </motion.div>
  )
}
