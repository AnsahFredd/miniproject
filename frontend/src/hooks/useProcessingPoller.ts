import axios from "axios"
import { useEffect, useRef, useState } from "react"
import toast from "react-hot-toast"

const API = import.meta.env.VITE_API_BASE_URL

// Global polling registry to prevent multiple polls for same document
const activePolls = new Set<string>()

export const pollProcessingStatus = (
  documentId: string,
  taskId: string,
  setProcessingStatus: any,
  setUploadResult: any,
  navigate: any
) => {
  // Prevent multiple polls for the same document
  const pollKey = `${documentId}-${taskId}`
  if (activePolls.has(pollKey)) {
    console.log(`Already polling for document ${documentId}`)
    return
  }
  
  activePolls.add(pollKey)
  
  let attempts = 0
  const maxAttempts = 60
  let currentDelay = 5000 // Start with 5 seconds
  const maxDelay = 30000   // Max 30 seconds between requests
  let timeoutId: ReturnType<typeof setTimeout>

  const cleanup = () => {
    activePolls.delete(pollKey)
    if (timeoutId) clearTimeout(timeoutId)
  }

  const checkStatus = async () => {
    try {
      const token = localStorage.getItem("token")
      const res = await axios.get(`${API}/documents/${documentId}/processing-status`, {
        headers: { Authorization: `Bearer ${token}` },
      })

      const status = res.data.data
      setProcessingStatus(status)

      if (status.processing_status === "completed") {
        setUploadResult({ type: "success", message: "AI analysis completed!" })
        toast.success("AI analysis completed!")
        cleanup()
        setTimeout(() => navigate(`/document/${documentId}/review`), 1500)
        return
      } 
      
      if (status.processing_status === "failed") {
        setUploadResult({
          type: "error",
          message: "Document uploaded but AI processing failed.",
        })
        cleanup()
        return
      }
      
      // Continue polling if still processing/pending
      if (attempts++ < maxAttempts) {
        // Reset delay on successful request
        currentDelay = 5000
        timeoutId = setTimeout(checkStatus, currentDelay)
      } else {
        // Max attempts reached
        setUploadResult({
          type: "error",
          message: "Processing timeout. Please check back later.",
        })
        cleanup()
      }

    } catch (error: any) {
      console.error("Polling error:", error)
      
      // Handle rate limiting specifically
      if (error.response?.status === 429) {
        // Exponential backoff for rate limiting
        currentDelay = Math.min(currentDelay * 2, maxDelay)
        console.log(`Rate limited. Waiting ${currentDelay/1000}s before retry`)
        
        if (attempts++ < maxAttempts) {
          timeoutId = setTimeout(checkStatus, currentDelay)
        } else {
          cleanup()
        }
        return
      }
      
      // Other errors - retry with backoff but limit attempts
      if (attempts++ < 3) {
        currentDelay = Math.min(currentDelay * 1.5, maxDelay)
        timeoutId = setTimeout(checkStatus, currentDelay)
      } else {
        setUploadResult({
          type: "error",
          message: "Unable to check processing status. Please refresh the page.",
        })
        cleanup()
      }
    }
  }

  // Start polling
  checkStatus()
  
  // Return cleanup function for manual cancellation
  return cleanup
}

// Alternative: Use this hook in your component for better lifecycle management
export const useProcessingStatusPoll = (
  documentId: string,
  taskId: string,
  shouldPoll: boolean = true,
  navigate: (path: string) => void // Pass navigate as a parameter
) => {
  const [processingStatus, setProcessingStatus] = useState(null)
  const [isPolling, setIsPolling] = useState(false)
  const cleanupRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    if (!shouldPoll || !documentId || !taskId) return

    setIsPolling(true)
    
    const cleanup = pollProcessingStatus(
      documentId,
      taskId,
      setProcessingStatus,
      (result) => {
        setIsPolling(false)
        // Handle result
      },
      navigate // Now navigate is defined
    )
    
    cleanupRef.current = cleanup ?? null

    return () => {
      if (cleanupRef.current) {
        cleanupRef.current()
      }
      setIsPolling(false)
    }
  }, [documentId, taskId, shouldPoll, navigate])

  return { processingStatus, isPolling }
}