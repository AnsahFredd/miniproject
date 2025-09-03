import { useState, useCallback } from "react"
import axios from "axios"
import toast from "react-hot-toast"
import { useNavigate } from "react-router-dom"
import { pollProcessingStatus }  from "./useProcessingPoller"

const API = import.meta.env.VITE_API_BASE_URL

export const useFileUpload = () => {
  const [uploadedFile, setUploadedFile] = useState<any | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [processingStatus, setProcessingStatus] = useState<any | null>(null)
  const [uploadResult, setUploadResult] = useState<any>({ type: null, message: "" })
  const navigate = useNavigate()

  const handleDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return
    setUploadedFile(file)
    setUploadResult({ type: null, message: "" })
    setProcessingStatus(null)
  }, [])

  const handleUpload = async () => {
    if (!uploadedFile) return
    const token = localStorage.getItem("token")
    if (!token) {
      setUploadResult({
        type: "error",
        message: "Authentication required. Please log in to upload documents.",
      })
      return
    }

    const formData = new FormData()
    formData.append("file", uploadedFile)

    try {
      setIsUploading(true)
      const res = await axios.post(`${API}/documents/upload`, formData, {
        headers: { Authorization: `Bearer ${token}` },
      })

      if (res.status === 202 && res.data.processing) {
        const documentId = res.data.data?.document_id
        const taskId = res.data.processing.task_id
        setUploadResult({ type: "processing", message: "AI analysis in progress..." })
        pollProcessingStatus(documentId, taskId, setProcessingStatus, setUploadResult, navigate)
      } else {
        const documentId = res.data.data?.document_id
        toast.success("Document uploaded successfully!")
        setUploadResult({ type: "success", message: "Document uploaded successfully!" })
        setTimeout(() => navigate(`/document/${documentId}/review`), 1500)
      }
    } catch (err: any) {
      setUploadResult({ type: "error", message: "Upload failed. Try again." })
    } finally {
      setIsUploading(false)
    }
  }

  const resetUpload = () => {
    setUploadedFile(null)
    setUploadResult({ type: null, message: "" })
    setProcessingStatus(null)
  }

  return {
    uploadedFile,
    isUploading,
    processingStatus,
    uploadResult,
    handleDrop,
    handleUpload,
    resetUpload,
  }
}
