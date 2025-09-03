import axios from "axios"
import toast from "react-hot-toast"
import type { DocumentStatus, QueueDocument } from "../types/processginQueueTypes"

const API = import.meta.env.VITE_API_BASE_URL

// Map API status to display status
export const mapApiStatusToDisplayStatus = (apiStatus: string): DocumentStatus => {
  const status = apiStatus?.toLowerCase()
  switch (status) {
    case "uploaded":
    case "pending":
      return "Uploaded"
    case "processing":
    case "in_progress":
    case "analyzing":
      return "Processing"
    case "completed":
    case "done":
    case "success":
    case "ready":
      return "Completed"
    case "failed":
    case "error":
    case "cancelled":
    case "canceled":
      return "Failed"
    default:
      return "Uploaded"
  }
}

// Fetch documents from API
export const fetchDocuments = async (token: string): Promise<QueueDocument[]> => {
  if (!token) {
    console.log("No token available for fetching documents")
    return []
  }

  try {
    const response = await axios.get(`${API}/documents/`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    })

    let docs: any[] = []
    if (response.data && Array.isArray(response.data.data)) {
      docs = response.data.data
    } else if (Array.isArray(response.data)) {
      docs = response.data
    } else {
      docs = []
    }

    const formattedDocs: QueueDocument[] = docs.map((doc: any) => ({
      id: doc.id || doc.document_id || doc._id,
      name: doc.name || doc.filename || doc.title || "Unknown Document",
      status: mapApiStatusToDisplayStatus(doc.status || doc.processing_status || doc.state),
      uploadedAt: doc.created_at || doc.uploaded_at || doc.createdAt || doc.upload_date,
      file_type: doc.file_type,
    }))

    return formattedDocs
  } catch (error: any) {
    console.error("Error fetching documents:", error)

    if (error.response?.status === 401) {
      toast.error("Authentication expired. Please log in again.")
    } else if (error.response?.status !== 429) {
      toast.error("Failed to load documents. Please try again.")
    }

    throw error
  }
}

// Cancel/remove document
export const cancelDocument = async (documentId: string, token: string): Promise<void> => {
  if (!token) return

  try {
    await axios.delete(`${API}/documents/${documentId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    toast.success("Document removed successfully")
  } catch (error) {
    console.error("Error cancelling document:", error)
    toast.error("Failed to cancel document processing")
    throw error
  }
}
