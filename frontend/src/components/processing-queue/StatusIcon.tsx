import type React from "react"
import { CheckCircle, XCircle, AlertCircle, Clock } from "lucide-react"
import type { StatusIconProps } from "../../types/processginQueueTypes"

const StatusIcon: React.FC<StatusIconProps> = ({ status }) => {
  switch (status) {
    case "Completed":
      return <CheckCircle className="w-4 h-4 text-green-600" />
    case "Processing":
      return <Clock className="w-4 h-4 text-blue-600 animate-pulse" />
    case "Failed":
      return <XCircle className="w-4 h-4 text-red-600" />
    case "Uploaded":
    default:
      return <AlertCircle className="w-4 h-4 text-gray-400" />
  }
}

export default StatusIcon
