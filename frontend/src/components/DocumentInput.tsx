import React from "react";
import { Loader2 } from "lucide-react";

interface DocumentInputProps {
  contractText: string;
  setContractText: (text: string) => void;
  loading: boolean;
  error: string;
  documentId?: string;
  onRetry: () => void;
}

const DocumentInput: React.FC<DocumentInputProps> = ({
  contractText,
  setContractText,
  loading,
  error,
  documentId,
  onRetry,
}) => {
  return (
    <div className="lg:col-span-2 bg-white rounded-lg shadow-sm border">
      <div className="p-6 border-b">
        <h2 className="text-xl font-semibold text-gray-900">
          Document Review
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          Review the processed document, analyze identified clauses, and
          access summaries.
        </p>
      </div>

      <div className="p-6">
        <div className="flex items-center gap-4 mb-4">
          <span className="text-sm font-medium text-gray-700">
            Original Formatting
          </span>
          <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
            Text-Only
          </span>
        </div>

        {loading ? (
          <div className="w-full h-64 border rounded-lg flex items-center justify-center">
            <div className="text-center">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-2" />
              <p className="text-sm text-gray-600">Loading document...</p>
            </div>
          </div>
        ) : (
          <textarea
            value={contractText}
            onChange={(e) => setContractText(e.target.value)}
            className="w-full h-64 p-4 border rounded-lg text-sm text-gray-700 leading-relaxed resize-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder={documentId ? "Document content will appear here..." : "Paste your contract text here..."}
            readOnly={!!documentId}
          />
        )}

        {error && (
          <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">{error}</p>
            {documentId && (
              <button
                onClick={onRetry}
                className="mt-2 text-sm text-red-600 hover:text-red-800 underline"
              >
                Try again
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentInput;