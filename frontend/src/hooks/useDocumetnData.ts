"use client"

import { useState, useEffect } from "react"
import axios from "axios"
import type { DocumentData, AnalysisData } from "../types/documentTypes"

export const useDocumentData = (documentId: string | undefined) => {
  const [documentData, setDocumentData] = useState<DocumentData | null>(null)
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const API = import.meta.env.VITE_API_BASE_URL

  const fetchDocument = async () => {
    if (!documentId) return null

    try {
      const token = localStorage.getItem("token") || localStorage.getItem("authToken")
      const response = await axios.get(`${API}/documents/${documentId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      })

      console.log("Fetched document data:", response.data.data)
      setDocumentData(response.data.data)
      return response.data.data
    } catch (err: any) {
      console.error("Error fetching document:", err)
      throw err
    }
  }

  const fetchDocumentAnalysis = async () => {
    if (!documentId) return

    try {
      const token = localStorage.getItem("token") || localStorage.getItem("authToken")
      const response = await axios.get(`${API}/documents/${documentId}/analysis`, {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      })

      console.log("Fetched analysis data:", response.data)
      setAnalysisData(response.data)
    } catch (err: any) {
      console.error("Error fetching document analysis:", err)
      // Don't set error here, analysis endpoint might not exist for all documents
    }
  }

  const initializeDocument = async () => {
    if (!documentId) return

    try {
      setLoading(true)
      setError("")

      // Fetch basic document data first
      const docData = await fetchDocument()

      if (docData?.processing_status === "completed") {
        // If processing is already complete, fetch analysis
        await fetchDocumentAnalysis()
      }
    } catch (err: any) {
      console.error("Error initializing document:", err)
      setError("Failed to load document data")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    initializeDocument()
  }, [documentId])

  return {
    documentData,
    analysisData,
    loading,
    error,
    refetchDocument: fetchDocument,
    refetchAnalysis: fetchDocumentAnalysis,
  }
}
