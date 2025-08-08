import React from "react";
import { Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';

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
            <Clock className="w-5 h-5 text-[var(--color-secondary)] animate-pulse" />
            <span className="text-[var(--color-secondary)] font-medium">Pending...</span>
          </>
        );
      case "processing":
        return (
          <>
            <Loader2 className="w-5 h-5 text-[var(--color-primary)] animate-spin" />
            <span className="text-[var(--color-primary)] font-medium">Processing...</span>
          </>
        );
      case "completed":
        return (
          <>
            <CheckCircle className="w-5 h-5 text-[var(--color-accent)]" />
            <span className="text-[var(--color-accent)] font-medium">Completed</span>
          </>
        );
      case "duplicated":
        return (
          <>
            <XCircle className="w-5 h-5 text-[var(--color-secondary)]" />
            <span className="text-[var(--color-secondary)] font-medium">Duplicate Document</span>
          </>
        );
      case "failed":
        return (
          <>
            <XCircle className="w-5 h-5 text-[var(--color-primary)]" />
            <span className="text-[var(--color-primary)] font-medium">
              Failed: {error || "Unknown error"}
            </span>
          </>
        );
      default:
        return null;
    }
  };

  return (
    <div className="flex items-center gap-2 p-2 bg-[var(--bg-soft)] rounded-md shadow-sm w-fit mx-auto mt-4" role="status" aria-live="polite">
      {renderStatus()}
    </div>
  );
};

export default ProcessingStatus;
