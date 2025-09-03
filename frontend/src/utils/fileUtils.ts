export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return "0 Bytes"
  const k = 1024
  const sizes = ["Bytes", "KB", "MB", "GB"]
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Number.parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
}

export const getProcessingMessage = (status: { stage?: string; message?: string }) => {
  const stageMessages: { [key: string]: string } = {
    starting: "Initializing AI analysis...",
    classifying: "Analyzing document type...",
    summarizing: "Generating summary...",
    embedding: "Creating embeddings...",
    complete: "AI analysis completed!",
  }
  return stageMessages[status.stage || ""] || status.message || "Processing..."
}
