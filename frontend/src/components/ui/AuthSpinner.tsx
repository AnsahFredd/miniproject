import React from "react";
import { Loader2 } from 'lucide-react';

interface AuthSpinnerProps {
  message: string;
  isVisible: boolean;
}

const AuthSpinner: React.FC<AuthSpinnerProps> = ({ message, isVisible }) => {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center backdrop-blur-soft" role="dialog" aria-modal="true" aria-label="Loading">
      <div className="flex flex-col items-center justify-center p-8 bg-white rounded-xl shadow-xl border animate-pop" role="status" aria-live="polite">
        <Loader2 className="w-12 h-12 animate-spin text-[var(--color-accent)] mb-4" aria-hidden="true" />
        <p className="text-lg font-medium text-[var(--color-primary)] text-center max-w-sm">
          {message}
        </p>
        <div className="mt-3 flex space-x-1" aria-hidden="true">
          <div className="w-2 h-2 bg-[var(--color-accent)] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-[var(--color-accent)] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-[var(--color-accent)] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  );
};

export default AuthSpinner;
