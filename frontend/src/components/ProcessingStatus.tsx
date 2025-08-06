import React from "react";
import { Loader2, CheckCircle, XCircle, Clock } from "lucide-react";

interface ProcessingStatusProps {
  status: "pending" | "processing" | "completed" | "failed" | "duplicated";
  error?: string | null;
}

const ProcessingStatus: React.FC<ProcessingStatusProps> = ({ status, error }) => {
  const renderStatus = () => {
    switch (status) {
      case "pending":
        return (
          <>
            <Clock className="w-5 h-5 text-yellow-500 animate-pulse" />
            <span className="text-yellow-600 font-medium">Pending...</span>
          </>
        );
      case "processing":
        return (
          <>
            <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
            <span className="text-blue-600 font-medium">Processing...</span>
          </>
        );
      case "completed":
        return (
          <>
            <CheckCircle className="w-5 h-5 text-green-500" />
            <span className="text-green-600 font-medium">Completed</span>
          </>
        );
      case "duplicated":
        return (
          <>
            <XCircle className="w-5 h-5 text-orange-500" />
            <span className="text-orange-600 font-medium">Duplicate Document</span>
          </>
        );
      case "failed":
        return (
          <>
            <XCircle className="w-5 h-5 text-red-500" />
            <span className="text-red-600 font-medium">
              Failed: {error || "Unknown error"}
            </span>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex items-center gap-2 p-2 bg-gray-100 rounded-md shadow-sm w-fit mx-auto mt-4">
      {renderStatus()}
    </div>
  );
};

export default ProcessingStatus;
