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
        
        console.log('Analyzing documents for expiry dates...'); // Debug log
        
        // First, get all uploaded documents - FIX THE ENDPOINT
        const documentsResponse = await axios.get(`${API}/documents/`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        console.log('Documents Response:', documentsResponse.data); // Debug log

        // Handle different response structures
        let documents: DocumentType[] = [];

        if (documentsResponse.data.documents) {
          documents = documentsResponse.data.documents;
        } else if (Array.isArray(documentsResponse.data)) {
          documents = documentsResponse.data;
        } else {
          console.error('Unexpected documents response format:', documentsResponse.data);
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
            console.log(`Analyzing document: ${doc.filename}`);
            
            // FIX THE API ENDPOINT AND REQUEST FORMAT
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
            console.log(`AI Analysis for ${doc.name || doc.filename}:`, aiResult);

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
            console.error(`Error analyzing document ${doc.name || doc.filename}:`, docError);
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
        console.error('Error analyzing documents for expiry:', error);
        console.error('Error response:', error.response?.data); // Debug log
        
        // Better error handling
        let errorMessage = 'Failed to analyze documents for expiry dates';
        
        if (error.response?.status === 405) {
          errorMessage = 'Documents API endpoint not found or method not allowed. Please check your backend configuration.';
        } else if (error.response?.status === 404) {
          errorMessage = 'Documents endpoint not found. Please ensure your backend is running and configured correctly.';
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
    console.log('Manual refresh triggered');
    if (!token) return;
    
    // Re-run the analysis
    setContractsData(prev => ({ ...prev, loading: true, error: null }));
    
    // Trigger useEffect by updating a state variable
    const event = new Event('refresh');
    window.dispatchEvent(event);
    
    // Or simply reload the component
    window.location.reload();
  };

  return (
    <div className="mb-8 mt-11 mx-11">
      <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold text-[#121417]">AI Recommendations</h2>
          <button
            onClick={handleRefresh}
            disabled={contractsData.loading}
            className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600 transition disabled:opacity-50"
          >
            {contractsData.loading ? 'Analyzing...' : 'Refresh'}
          </button>
        </div>
        
        
        {/* Expiring Contracts Alert */}
        {contractsData.loading ? (
          <div className="flex items-center justify-center bg-gray-100 rounded-lg p-6 h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#4A9B8E]"></div>
            <span className="ml-3 text-gray-600">Analyzing documents for expiry dates...</span>
          </div>
        ) : contractsData.error ? (
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-red-800">{contractsData.error}</p>
              </div>
            </div>
          </div>
        ) : contractsData.expiringCount > 0 ? (
          <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between bg-gradient-to-r from-[#4A9B8E] to-[#5BAE9F] rounded-lg p-6 text-white">
            <div className="flex-1 mb-4 lg:mb-0">
              <h3 className="text-xl font-semibold mb-2">
                {contractsData.expiringCount} contract{contractsData.expiringCount !== 1 ? 's' : ''} expiring soon
              </h3>
              <p className="text-white/90 mb-3">Review and take action</p>
              
              {/* Show some contract details */}
              {contractsData.contracts.length > 0 && (
                <div className="text-sm text-white/80">
                  <p className="mb-1">Next expiring:</p>
                  <ul className="space-y-1">
                    {contractsData.contracts.slice(0, 2).map((contract, index) => (
                      <li key={index} className="flex justify-between items-center">
                        <span className="truncate mr-4">
                          {contract.name || contract.title || contract.document_name || 'Unnamed Contract'}
                        </span>
                        <span className="flex-shrink-0 font-medium">
                          {contract.days_until_expiry !== undefined 
                            ? `${contract.days_until_expiry} day${contract.days_until_expiry !== 1 ? 's' : ''}`
                            : new Date(contract.expiry_date).toLocaleDateString()
                          }
                        </span>
                      </li>
                    ))}
                  </ul>
                  {contractsData.contracts.length > 2 && (
                    <p className="mt-2 text-white/70">
                      +{contractsData.contracts.length - 2} more contracts
                    </p>
                  )}
                </div>
              )}
            </div>
            
            {/* Contract Document Illustration */}
            <div className="flex-shrink-0">
              <div className="relative">
                {/* Document background */}
                <div className="w-24 h-32 bg-white rounded-lg shadow-lg transform rotate-3">
                  {/* Document lines */}
                  <div className="p-3 space-y-2">
                    <div className="h-1 bg-gray-300 rounded w-full"></div>
                    <div className="h-1 bg-gray-300 rounded w-3/4"></div>
                    <div className="h-1 bg-gray-300 rounded w-full"></div>
                    <div className="h-1 bg-gray-300 rounded w-1/2"></div>
                  </div>
                </div>
                
                {/* Pen illustration */}
                <div className="absolute -bottom-2 -right-2 w-16 h-3 bg-gray-700 rounded-full transform rotate-45 shadow-md">
                  <div className="absolute right-0 top-0 w-4 h-3 bg-gray-800 rounded-r-full"></div>
                  <div className="absolute right-3 top-0.5 w-1 h-2 bg-yellow-400 rounded-full"></div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-green-800">All contracts are up to date! No expiring contracts found in your documents.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AIRecommendations;