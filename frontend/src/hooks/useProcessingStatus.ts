"use client"

import { useState, useEffect, useRef, useCallback } from "react"
import axios from "axios"
import type { ProcessingStatus } from "../types/documentTypes"

export const useProcessingStatus = (
  documentId: string | undefined,
  onComplete?: () => void
) => {
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null)
  const [pollCount, setPollCount] = useState(0)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const API = import.meta.env.VITE_API_BASE_URL

  const fetchProcessingStatus = useCallback(async () => {
    if (!documentId) return null

    try {
      const token = localStorage.getItem("token") || localStorage.getItem("authToken")
      const response = await axios.get(`${API}/documents/${documentId}/processing-status`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      })

      setProcessingStatus(response.data.data)
      return response.data.data as ProcessingStatus
    } catch (err: any) {
      console.error("Error fetching processing status:", err)
      return null
    }
  }, [API, documentId])

  const pollProcessingStatus = useCallback(async () => {
    if (!documentId || pollCount > 60) return // Stop after ~5 mins

    const status = await fetchProcessingStatus()
    if (!status) return

    if (status.processing_status === "completed") {
      onComplete?.()
      return
    }

    if (status.processing_status === "processing" || status.processing_status === "pending") {
      setPollCount((prev) => prev + 1)
      timeoutRef.current = setTimeout(pollProcessingStatus, 5000) // Poll every 5s
    }
  }, [documentId, pollCount, fetchProcessingStatus, onComplete])

  useEffect(() => {
    if (documentId) {
      fetchProcessingStatus()
    }

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current) // cleanup on unmount
    }
  }, [documentId, fetchProcessingStatus])

  return {
    processingStatus,
    startPolling: pollProcessingStatus,
    fetchStatus: fetchProcessingStatus,
  }
}
