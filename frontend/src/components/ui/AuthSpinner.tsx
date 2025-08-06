import React from "react";
import { Loader2 } from "lucide-react";

interface AuthSpinnerProps {
  message: string;
  isVisible: boolean;
}

const AuthSpinner: React.FC<AuthSpinnerProps> = ({ message, isVisible }) => {
  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-white bg-opacity-95 backdrop-blur-sm">
      <div className="flex flex-col items-center justify-center p-8 bg-white rounded-lg shadow-lg border">
        <Loader2 className="w-12 h-12 animate-spin text-black mb-4" />
        <p className="text-lg font-medium text-gray-800 text-center max-w-sm">
          {message}
        </p>
        <div className="mt-3 flex space-x-1">
          <div className="w-2 h-2 bg-black rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-black rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-black rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  );
};

export default AuthSpinner;