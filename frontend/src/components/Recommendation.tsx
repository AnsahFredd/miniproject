import React, { useEffect, useState } from "react";
import axios from "axios";

// Type definitions
interface Contract {
  id: string | number;
  name?: string;
  title?: string;
  expiry_date: string;
  days_until_expiry?: number;
  document_name?: string;
}

export interface DocumentType {
  _id?: string;
  id?: string;
  filename?: string;
  name?: string;
  title?: string;
  content?: string;
  status?: string;
  createdAt?: string;
}

interface ContractsData {
  expiringCount: number;
  contracts: Contract[];
  loading: boolean;
  error: string | null;
}

interface AIRecommendationsProps {
  token: string;
}

const API = import.meta.env.VITE_API_BASE_URL;

const AIRecommendations: React.FC<AIRecommendationsProps> = ({ token }) => {
  const [contractsData, setContractsData] = useState<ContractsData>({
    expiringCount: 0,
    contracts: [],
    loading: true,
    error: null
  });

  // Extract expiry dates from documents
  useEffect(() => {
    const analyzeDocumentsForExpiry = async () => {
      if (!token) return;

      try {
        setContractsData(prev => ({ ...prev, loading: true, error: null }));
        
        // First, get all uploaded documents
        const documentsResponse = await axios.get(`${API}/documents/`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        // Handle different response structures
        let documents: DocumentType[] = [];

        if (documentsResponse.data.documents) {
          documents = documentsResponse.data.documents;
        } else if (Array.isArray(documentsResponse.data)) {
          documents = documentsResponse.data;
        } else {
          throw new Error('Unexpected response format from documents API');
        }
        
        if (documents.length === 0) {
          setContractsData({
            expiringCount: 0,
            contracts: [],
            loading: false,
            error: null
          });
          return;
        }

        // Analyze each document for expiry dates using AI
        const contractsWithExpiry: Contract[] = [];
        
        for (const doc of documents) {
          try {
            const analysisResponse = await axios.post(`${API}/expiry/extract-expiry`, {
              document_id: doc._id || doc.id, // Handle both _id and id formats
              prompt: `Analyze this document and extract any contract expiry dates, termination dates, or validity periods. 
                      Look for phrases like "expires on", "valid until", "termination date", "end date", etc. 
                      Return the date in YYYY-MM-DD format if found, or null if no expiry date is found.
                      Also extract the contract name or title if available.`
            }, {
              headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
              }
            });

            const aiResult = analysisResponse.data;

            if (aiResult.expiry_date) {
              const expiryDate = new Date(aiResult.expiry_date);
              const today = new Date();
              const timeDiff = expiryDate.getTime() - today.getTime();
              const daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24));

              // Only include contracts expiring in the next 30 days
              if (daysDiff <= 30 && daysDiff >= 0) {
                contractsWithExpiry.push({
                  id: (doc._id || doc.id) ?? "unknown-id",
                  name: aiResult.contract_name || doc.name || doc.filename,
                  title: aiResult.contract_title,
                  expiry_date: aiResult.expiry_date,
                  days_until_expiry: daysDiff,
                  document_name: doc.name || doc.filename
                });
              }
            }
          } catch (docError: any) {
            // Continue with other documents even if one fails
          }
        }

        // Sort by days until expiry (most urgent first)
        contractsWithExpiry.sort((a, b) => (a.days_until_expiry || 0) - (b.days_until_expiry || 0));

        setContractsData({
          expiringCount: contractsWithExpiry.length,
          contracts: contractsWithExpiry,
          loading: false,
          error: null
        });

      } catch (error: any) {
        let errorMessage = 'Failed to analyze documents for expiry dates';
        
        if (error.response?.status === 405) {
          errorMessage = 'Documents API endpoint not found or method not allowed.';
        } else if (error.response?.status === 404) {
          errorMessage = 'Documents endpoint not found.';
        } else if (error.response?.status === 401) {
          errorMessage = 'Authentication failed. Please log in again.';
        } else if (error.response?.data?.detail) {
          errorMessage = error.response.data.detail;
        } else if (error.message) {
          errorMessage = error.message;
        }
        
        setContractsData(prev => ({
          ...prev,
          loading: false,
          error: errorMessage
        }));
      }
    };

    analyzeDocumentsForExpiry();
  }, [token]);

  const handleRefresh = async () => {
    window.location.reload();
  };

  return (
    <div className="card p-6 mt-11 mx-11">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-[var(--color-primary)]">AI Recommendations</h2>
        <button
          onClick={handleRefresh}
          disabled={contractsData.loading}
          className="px-3 py-1 text-sm btn btn-outline-accent"
        >
          {contractsData.loading ? 'Analyzing...' : 'Refresh'}
        </button>
      </div>
      
      {contractsData.loading ? (
        <div className="flex items-center justify-center bg-[var(--bg-soft)] rounded-lg p-6 h-32 border border-gray-200" role="status" aria-live="polite">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-accent)]"></div>
          <span className="ml-3 text-[var(--color-secondary)]">Analyzing documents for expiry dates...</span>
        </div>
      ) : contractsData.error ? (
        <div className="bg-[color:rgb(20_184_166_/_10%)] border border-[color:rgb(20_184_166_/_26%)] rounded-lg p-6" role="alert" aria-live="assertive">
          <div className="text-[var(--color-primary)]">
            <p className="text-sm">{contractsData.error}</p>
          </div>
        </div>
      ) : contractsData.expiringCount > 0 ? (
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between bg-[color:rgb(20_184_166_/_12%)] rounded-lg p-6 text-[var(--color-primary)] border border-[color:rgb(20_184_166_/_26%)]">
          <div className="flex-1 mb-4 lg:mb-0">
            <h3 className="text-xl font-semibold mb-2">
              {contractsData.expiringCount} contract{contractsData.expiringCount !== 1 ? 's' : ''} expiring soon
            </h3>
            <p className="text-[var(--color-secondary)] mb-3">Review and take action</p>
            
            {contractsData.contracts.length > 0 && (
              <div className="text-sm text-[var(--color-secondary)]">
                <p className="mb-1 font-medium text-[var(--color-primary)]">Next expiring:</p>
                <ul className="space-y-1">
                  {contractsData.contracts.slice(0, 2).map((contract, index) => (
                    <li key={index} className="flex justify-between items-center bg-white rounded px-3 py-1 border border-gray-200">
                      <span className="truncate mr-4 font-medium text-[var(--color-primary)]">
                        {contract.name || contract.title || contract.document_name || 'Unnamed Contract'}
                      </span>
                      <span className="flex-shrink-0 font-bold text-[var(--color-primary)]">
                        {contract.days_until_expiry !== undefined 
                          ? `${contract.days_until_expiry} day${contract.days_until_expiry !== 1 ? 's' : ''}`
                          : new Date(contract.expiry_date).toLocaleDateString()
                        }
                      </span>
                    </li>
                  ))}
                </ul>
                {contractsData.contracts.length > 2 && (
                  <p className="mt-2 text-[var(--color-secondary)] font-medium">
                    +{contractsData.contracts.length - 2} more contracts
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Illustration remains visual only */}
          <div className="flex-shrink-0">
            <div className="relative" aria-hidden="true">
              <div className="w-24 h-32 bg-white rounded-lg shadow-lg transform rotate-3 border border-gray-200">
                <div className="p-3 space-y-2">
                  <div className="h-1 bg-gray-400 rounded w-full"></div>
                  <div className="h-1 bg-gray-400 rounded w-3/4"></div>
                  <div className="h-1 bg-gray-400 rounded w-full"></div>
                  <div className="h-1 bg-gray-400 rounded w-1/2"></div>
                </div>
              </div>
              <div className="absolute -bottom-2 -right-2 w-16 h-3 bg-gray-700 rounded-full transform rotate-45 shadow-md">
                <div className="absolute right-0 top-0 w-4 h-3 bg-gray-800 rounded-r-full"></div>
                <div className="absolute right-3 top-0.5 w-1 h-2 bg-[var(--color-accent)] rounded-full"></div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-[color:rgb(20_184_166_/_10%)] border border-[color:rgb(20_184_166_/_26%)] rounded-lg p-6 text-[var(--color-primary)]">
          <div className="flex items-center">
            <div className="ml-3">
              <p className="text-sm">All contracts are up to date! No expiring contracts found in your documents.</p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AIRecommendations;
