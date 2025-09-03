import { Loader2 } from "lucide-react"
import { getProcessingMessage } from "../../utils/fileUtils"

type Props = {
  status: {
    stage?: string
    progress?: number
    message?: string
  }
}

const ProcessingStatusView = ({ status }: Props) => (
  <div className="mt-4 space-y-3">
    <div className="flex items-center gap-2">
      <Loader2 className="w-4 h-4 text-black animate-spin" />
      <span className="text-sm text-[#0f766e]">{getProcessingMessage(status)}</span>
    </div>

    {status.progress && (
      <div className="w-full h-2 bg-gray-200 rounded-full">
        <div
          className="h-2 transition-all duration-300 bg-[#0f766e] rounded-full"
          style={{ width: `${status.progress}%` }}
        />
      </div>
    )}

    <p className="text-sm text-black" >
      This usually takes 2-5 minutes. You can safely leave this page and check back later.
    </p>
  </div>
)

export default ProcessingStatusView