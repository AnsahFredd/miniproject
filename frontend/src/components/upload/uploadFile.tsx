import { Card } from "../ui/card"
import UploadDropzone from "./UploadDropzone"
import SelectedFileCard from "./SelectedFielCard"
import UploadResultAlert from "./UploadResultAlert"
import { useFileUpload } from "../../hooks/useFileUpload"
import { useEffect } from "react"

const UploadFile = () => {
  const {
    uploadedFile,
    uploadResult,
    isUploading,
    processingStatus,
    handleDrop,
    handleUpload,
    resetUpload,
  } = useFileUpload()

  // Add this to useFileUpload.ts
useEffect(() => {
  let pollInterval: ReturnType<typeof setInterval>
  
  if (uploadResult.type === 'success' && uploadResult.documentId && 
      processingStatus?.processing_status !== 'completed' && 
      processingStatus?.processing_status !== 'failed') {
    
    pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/documents/${uploadResult.documentId}/processing-status`)
        const data = await response.json()
        processingStatus(data.data)
        
        if (data.data.processing_status === 'completed' || data.data.processing_status === 'failed') {
          clearInterval(pollInterval)
        }
      } catch (error) {
        console.error('Error polling status:', error)
      }
    }, 5000) // Poll every 5 seconds
  }
  
  return () => {
    if (pollInterval) clearInterval(pollInterval)
  }
}, [uploadResult, processingStatus?.processing_status])

  return (
    <div className="container mx-auto max-w-4xl p-6">
      <h1 className="text-3xl font-bold mb-2">Upload Legal Document</h1>
      <p className="text-gray-600 mb-6">
        Upload your legal contract for AI-powered analysis and validation
      </p>

      {uploadResult.type && (
        <UploadResultAlert
          result={uploadResult}
          processingStatus={processingStatus}
          onReset={resetUpload}
        />
      )}

      {!uploadedFile && !uploadResult.type && (
        <Card className="mb-6">
          <UploadDropzone onDrop={handleDrop} />
        </Card>
      )}

      {uploadedFile && !uploadResult.type && (
        <SelectedFileCard
          file={uploadedFile}
          isUploading={isUploading}
          onRemove={resetUpload}
          onUpload={handleUpload}
        />
      )}
    </div>
  )
}

export default UploadFile
