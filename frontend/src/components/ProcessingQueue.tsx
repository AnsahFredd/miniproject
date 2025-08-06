import React, { useState, useEffect } from 'react';
import { File, X, Eye } from 'lucide-react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

type DocumentStatus = 'Uploaded' | 'Processing' | 'Completed' | 'Failed';

type QueueDocument = {
  id: string;
  name: string;
  status: DocumentStatus;
  uploadedAt?: string;
};

interface ProcessingQueueProps {
  onDocumentUpdate?: () => void;
}

const API = import.meta.env.VITE_API_BASE_URL;

const ProcessingQueue: React.FC<ProcessingQueueProps> = ({ onDocumentUpdate }) => {
  const [documents, setDocuments] = useState<QueueDocument[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const navigate = useNavigate();

  // Fetch documents from API
  const fetchDocuments = async () => {
    const token = localStorage.getItem('token');
    const userId = localStorage.getItem('user_id');

    if (!token || !userId) return;

    setIsLoading(true);
    try {
      const response = await axios.get(`${API}/documents/`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.data && Array.isArray(response.data)) {
        const formattedDocs: QueueDocument[] = response.data.map((doc: any) => {
          console.log('Raw document from API:', doc);
          return {
            id: doc.id || doc.document_id || doc._id,
            name: doc.name || doc.filename || doc.title || 'Unknown Document',
            status: mapApiStatusToDisplayStatus(doc.status || doc.processing_status || doc.state),
            uploadedAt: doc.created_at || doc.uploaded_at || doc.createdAt,
          };
        });
        
        console.log('Formatted documents:', formattedDocs);
        setDocuments(formattedDocs);
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // Map API status to display status
  const mapApiStatusToDisplayStatus = (apiStatus: string): DocumentStatus => {
    const status = apiStatus?.toLowerCase();
    console.log('Mapping API status:', apiStatus, 'to display status');
    
    switch (status) {
      case 'uploaded':
      case 'pending':
        return 'Uploaded';
      case 'processing':
      case 'in_progress':
      case 'analyzing':
        return 'Processing';
      case 'completed':
      case 'complete':
      case 'done':
      case 'finished':
      case 'processed':
      case 'ready':
      case 'success':
      case 'successful':
        return 'Completed';
      case 'failed':
      case 'error':
      case 'cancelled':
      case 'canceled':
        return 'Failed';
      default:
        console.log('Unknown status, defaulting to Completed:', apiStatus);
        return 'Completed'; // Default to completed instead of uploaded
    }
  };

  // Get status styling
  const getStatusStyling = (status: DocumentStatus) => {
    switch (status) {
      case 'Uploaded':
        return 'bg-blue-100 text-blue-800';
      case 'Processing':
        return 'bg-yellow-100 text-yellow-800';
      case 'Completed':
        return 'bg-green-100 text-green-800';
      case 'Failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  // Handle document actions
  const handleViewDocument = (documentId: string) => {
    navigate(`/document/${documentId}/review`);
  };

  const handleCancelDocument = async (documentId: string) => {
    const token = localStorage.getItem('token');
    if (!token) return;

    try {
      await axios.delete(`${API}/documents/${documentId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      
      // Remove from local state
      setDocuments(prev => prev.filter(doc => doc.id !== documentId));
      
      // Notify parent component if needed
      if (onDocumentUpdate) {
        onDocumentUpdate();
      }
    } catch (error) {
      console.error('Error cancelling document:', error);
      alert('Failed to cancel document processing');
    }
  };

  // Fetch documents on component mount
  useEffect(() => {
    fetchDocuments();
  }, []);

  // Auto-refresh every 10 seconds for processing documents
  useEffect(() => {
    const hasProcessingDocs = documents.some(doc => doc.status === 'Processing');
    
    if (hasProcessingDocs) {
      const interval = setInterval(fetchDocuments, 10000); // 10 seconds
      return () => clearInterval(interval);
    }
  }, [documents]);

  // Don't render if no documents
  if (documents.length === 0) {
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto mt-8 p-6 bg-white border border-gray-200 rounded-lg">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Processing Queue</h2>
      
      {isLoading ? (
        <div className="text-center py-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900 mx-auto"></div>
          <p className="text-sm text-gray-500 mt-2">Loading documents...</p>
        </div>
      ) : (
        <div className="space-y-3">
          {/* Header */}
          <div className="grid grid-cols-3 gap-4 px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide border-b border-gray-200">
            <div>Document Name</div>
            <div className="text-center">Status</div>
            <div className="text-center">Actions</div>
          </div>

          {/* Document rows */}
          {documents.map((doc) => (
            <div
              key={doc.id}
              className="grid grid-cols-3 gap-4 items-center px-3 py-3 bg-gray-50 rounded-md border border-gray-200 hover:bg-gray-100 transition-colors"
            >
              {/* Document name */}
              <div className="flex items-center min-w-0">
                <File className="h-4 w-4 text-gray-400 mr-2 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-900 truncate">
                  {doc.name}
                </span>
              </div>

              {/* Status */}
              <div className="flex justify-center">
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusStyling(
                    doc.status
                  )}`}
                >
                  {doc.status}
                </span>
              </div>

              {/* Actions */}
              <div className="flex justify-center space-x-2">
                {(doc.status === 'Completed' || doc.status === 'Failed') ? (
                  <button
                    onClick={() => handleViewDocument(doc.id)}
                    className="inline-flex items-center px-2 py-1 text-xs font-medium text-blue-600 hover:text-blue-800 transition-colors"
                  >
                    <Eye className="h-3 w-3 mr-1" />
                    View Document
                  </button>
                ) : (
                  <button
                    onClick={() => handleCancelDocument(doc.id)}
                    className="inline-flex items-center px-2 py-1 text-xs font-medium text-red-600 hover:text-red-800 transition-colors"
                  >
                    <X className="h-3 w-3 mr-1" />
                    Cancel
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ProcessingQueue;