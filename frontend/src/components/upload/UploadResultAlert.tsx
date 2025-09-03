import { Alert, AlertDescription } from "../ui/alert"
import { CheckCircle, Clock, XCircle, ArrowRight, AlertCircle } from "lucide-react"
import Button from "../ui/Button"
import ProcessingStatusView from "./ProcessingStatusView"

type ValidationResult = {
  contractType: string
  confidence: number
  missingElements: string[]
  foundElements: string[]
}

type UploadResult = {
  type: "success" | "error" | "processing" | null
  message: string
  details?: ValidationResult
  suggestions?: string[]
  documentId?: string
}

type ProcessingStatus = {
  processing_status: 'pending' | 'processing' | 'completed' | 'failed'
  task_info?: {
    stage?: string
    progress?: number
    message?: string
  }
  processing_error?: string
}

type Props = {
  result: UploadResult
  processingStatus?: ProcessingStatus 
  onReset: () => void
}

const UploadResultAlert = ({ result, processingStatus, onReset }: Props) => {
  // Determine the actual status based on processing status
  const isProcessingComplete = processingStatus?.processing_status === 'completed'
  const isProcessingFailed = processingStatus?.processing_status === 'failed'
  const isProcessing = processingStatus?.processing_status === 'processing' || processingStatus?.processing_status === 'pending'

  // Override result type based on actual processing status
  const actualType = isProcessingComplete ? 'success' : 
                     isProcessingFailed ? 'error' : 
                     isProcessing ? 'processing' : 
                     result.type

  const getAlertStyles = () => {
    switch (actualType) {
      case 'success':
        return isProcessingComplete ? 'border-green-200 bg-green-50' : 'border-[#0FA596] bg-white'
      case 'error':
        return 'border-red-200 bg-red-50'
      case 'processing':
        return 'border-[#0FA596] bg-[#fff]'
      default:
        return 'border-gray-200 bg-gray-50'
    }
  }

  const getIcon = () => {
    if (isProcessingComplete) {
      return <CheckCircle className="h-5 w-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
    }
    if (isProcessingFailed) {
      return <AlertCircle className="h-5 w-5 text-red-600 mr-3 mt-0.5 flex-shrink-0" />
    }
    if (isProcessing) {
      return <Clock className="h-5 w-5 text-[#0f766e] mr-3 mt-0.5 flex-shrink-0" />
    }
    
    switch (result.type) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
      case 'error':
        return <XCircle className="h-5 w-5 text-red-600 mr-3 mt-0.5 flex-shrink-0" />
      default:
        return <Clock className="h-5 w-5 text-[#0f766e] mr-3 mt-0.5 flex-shrink-0" />
    }
  }

  const getTextColor = () => {
    if (isProcessingComplete) return 'text-green-800'
    if (isProcessingFailed) return 'text-red-800'
    if (isProcessing) return 'text-[#0f766e]'
    
    switch (result.type) {
      case 'success':
        return 'text-green-800'
      case 'error':
        return 'text-red-800'
      default:
        return 'text-[#0f766e]'
    }
  }

  const getMessage = () => {
    if (isProcessingComplete) {
      return 'Document Analysis Complete!'
    }
    if (isProcessingFailed) {
      return `Processing Failed: ${processingStatus?.processing_error || 'An error occurred during analysis'}`
    }
    if (isProcessing) {
      return result.message || 'Document uploaded successfully - AI analysis in progress'
    }
    return result.message
  }

  const handleViewDocument = () => {
    if (result.documentId) {
      window.location.href = `/documents/${result.documentId}`
    }
  }

  return (
    <Alert className={`mb-6 ${getAlertStyles()}`}>
      <div className="flex items-start">
        {getIcon()}

        <div className="flex-1">
          <AlertDescription className={`font-medium ${getTextColor()}`}>
            {getMessage()}
          </AlertDescription>

          {/* Show processing status while processing */}
          {isProcessing && processingStatus?.task_info && (
            <ProcessingStatusView status={processingStatus.task_info} />
          )}

          {/* Show success actions when completed */}
          {isProcessingComplete && (
            <div className="mt-3 space-y-2">
              <p className="text-sm text-green-700">
                Your document has been analyzed and is ready for review.
              </p>
              <div className="flex gap-2">
                <Button 
                  onClick={handleViewDocument}
                  label="View Analysis"
                  className="flex items-center gap-1 text-white bg-green-600 hover:bg-green-700"
                />
                <Button 
                  onClick={onReset} 
                  label="Upload Another"
                  className="text-green-600 border-green-600 hover:bg-green-50"
                />
              </div>
            </div>
          )}

          {/* Show error details and suggestions */}
          {(result.type === "error" || isProcessingFailed) && (
            <div className="mt-4 space-y-3">
              {result.details && (
                <div>
                  <p className="text-sm font-semibold text-gray-700">
                    Contract Type: {result.details.contractType} | Confidence:{" "}
                    {Math.round(result.details.confidence * 100)}%
                  </p>
                </div>
              )}
              
              {(result.suggestions ?? []).length > 0 && (
                <div className="p-3 mt-4 bg-green-200 border border-blue-200 rounded-lg">
                  <h4 className="mb-2 font-semibold text-black">How to fix this:</h4>
                  <ul className="list-disc list-inside space-y-1 text-[#0FA596] text-sm">
                    {result.suggestions?.map((suggestion, index) => (
                      <li key={index}>{suggestion}</li>
                    ))}
                  </ul>
                </div>
              )}
              
              <Button 
                onClick={onReset} 
                label="Try Another Document" 
                className="btn .btn-outline-accent text-black .btn-outline-accent:hover"
              />
            </div>
          )}

          {/* Show redirect message for original success (before processing complete) */}
          {result.type === "success" && !isProcessingComplete && !isProcessing && (
            <p className="text-sm text-[#0FA596] mt-2 flex items-center">
              Redirecting to document review... <ArrowRight className="w-4 h-4 ml-1" />
            </p>
          )}
        </div>
      </div>
    </Alert>
  )
}

export default UploadResultAlert