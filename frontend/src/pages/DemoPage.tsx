import { useState, useEffect } from 'react';
import axios from 'axios';

// Define TypeScript interfaces for the API response
interface Validation {
  contract_type?: string;
  confidence?: number;
  is_valid?: boolean;
}

interface Classification {
  document_type?: string;
  legal_domain?: string;
  urgency?: 'high' | 'medium' | 'low';
  extracted_entities?: any[];
}

interface DemoData {
  title: string;
  processing_success: boolean;
  validation?: Validation;
  classification?: Classification;
  tags?: string[];
  summary?: string;
  clauses?: string[];
  note?: string;
  rejection_reason?: string;
}

const API = import.meta.env.VITE_API_BASE_URL

const DemoPage = () => {
  const [demoData, setDemoData] = useState<DemoData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDemoData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Try the main demo endpoint first, fall back to mock if needed
      let response;
      try {
        response = await axios.get(`${API}/demo`);
      } catch (err) {
        console.log('Main demo failed, trying mock endpoint');
        response = await axios.get(`${API}/demo/mock`);
      }
      
      const data: DemoData = response.data;
      setDemoData(data);
    } catch (err) {
      console.error('Demo fetch error:', err);
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.message || err.message || 'An error occurred');
      } else {
        setError(err instanceof Error ? err.message : 'An error occurred');
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDemoData();
  }, []);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-lg text-gray-600">Processing demo contract with AI...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h2 className="text-lg font-semibold text-red-800">Demo Error</h2>
          <p className="text-red-600 mt-2">{error}</p>
          <button 
            onClick={fetchDemoData}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!demoData) {
    return (
      <div className="max-w-4xl mx-auto p-6">
        <p className="text-gray-600">No demo data available.</p>
      </div>
    );
  }

  const validation = demoData.validation || {};
  const classification = demoData.classification || {};
  const tags = demoData.tags || [];

  return (
    <div className="max-w-4xl mt-12 mx-auto p-6 space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {demoData.title}
        </h1>
        <p className="text-gray-600">
          AI-powered legal document analysis demo
        </p>
        
        {/* Status Badge */}
        <div className="mt-4 flex justify-center">
          {demoData.processing_success ? (
            <div className="px-4 py-2 bg-green-100 text-green-800 rounded-full flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="#14B8A6" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Contract Successfully Validated
            </div>
          ) : (
            <div className="px-4 py-2 bg-red-100 text-red-800 rounded-full flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="#14B8A6" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              Validation Failed
            </div>
          )}
        </div>
        
        {demoData.note && (
          <div className="mt-2 px-3 py-1 bg-[white] text-[#14B8A6] text-sm rounded-full inline-block">
            {demoData.note}
          </div>
        )}
      </div>

      {/* Validation Results */}
      {validation && Object.keys(validation).length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
          <div className="flex items-center mb-4">
            <div className="w-8 h-8 bg-[#F8FAFC] rounded-lg flex items-center justify-center mr-3">
              <svg className="w-5 h-5" fill="none" stroke="#14B8A6" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900">Contract Validation</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {validation.contract_type && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Contract Type</p>
                <p className="font-semibold capitalize">{validation.contract_type.replace('_', ' ')}</p>
              </div>
            )}
            {validation.confidence !== undefined && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Confidence</p>
                <p className="font-semibold">{(validation.confidence * 100).toFixed(1)}%</p>
              </div>
            )}
            {validation.is_valid !== undefined && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Valid Contract</p>
                <p className={`font-semibold ${validation.is_valid ? 'text-green-600' : 'text-red-600'}`}>
                  {validation.is_valid ? 'Yes' : 'No'}
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Summary Section */}
      {demoData.summary && (
        <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
          <div className="flex items-center mb-4">
            <div className="w-8 h-8 bg-[#F8FAFC] rounded-lg flex items-center justify-center mr-3">
              <svg className="w-5 h-5" fill="none" stroke="#14B8A6" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900">AI-Generated Summary</h2>
          </div>
          <p className="text-gray-700 leading-relaxed">{demoData.summary}</p>
        </div>
      )}

      {/* Classification Results */}
      {classification && Object.keys(classification).length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
          <div className="flex items-center mb-4">
            <div className="w-8 h-8 bg-[#F8FAFC] rounded-lg flex items-center justify-center mr-3">
              <svg className="w-5 h-5" fill="none" stroke="#14B8A6" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.99 1.99 0 013 12V7a4 4 0 014-4z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900">AI Classification</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {classification.document_type && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Document Type</p>
                <p className="font-semibold capitalize">{classification.document_type.replace('_', ' ')}</p>
              </div>
            )}
            {classification.legal_domain && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Legal Domain</p>
                <p className="font-semibold capitalize">{classification.legal_domain.replace('_', ' ')}</p>
              </div>
            )}
            {classification.urgency && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Urgency Level</p>
                <p className={`font-semibold capitalize ${
                  classification.urgency === 'high' ? 'text-red-600' : 
                  classification.urgency === 'medium' ? 'text-yellow-600' : 'text-green-600'
                }`}>
                  {classification.urgency}
                </p>
              </div>
            )}
            {classification.extracted_entities && (
              <div className="bg-gray-50 p-3 rounded-lg">
                <p className="text-sm text-gray-600">Entities Found</p>
                <p className="font-semibold">{classification.extracted_entities.length} entities</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Key Clauses Section */}
      {demoData.clauses && demoData.clauses.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
          <div className="flex items-center mb-4">
            <div className="w-8 h-8 bg-[#F8FAFC] rounded-lg flex items-center justify-center mr-3">
              <svg className="w-5 h-5" fill="none" stroke="#14B8A6" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900">Key Information Extracted</h2>
          </div>
          <div className="space-y-3">
            {demoData.clauses.map((clause, index) => (
              <div key={index} className="flex items-start">
                <div className="flex-shrink-0 w-6 h-6 bg-gray-100 rounded-full flex items-center justify-center mr-3 mt-0.5">
                  <span className="text-sm font-medium text-gray-600">{index + 1}</span>
                </div>
                <p className="text-gray-700">{clause}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tags Section */}
      {tags && tags.length > 0 && (
        <div className="bg-white p-6 rounded-xl shadow-lg border border-gray-200">
          <div className="flex items-center mb-4">
            <div className="w-8 h-8 bg-[#F8FAFC] rounded-lg flex items-center justify-center mr-3">
              <svg className="w-5 h-5" fill="none" stroke="#14B8A6" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.99 1.99 0 013 12V7a4 4 0 014-4z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900">Auto-Generated Tags</h2>
          </div>
          <div className="flex flex-wrap gap-2">
            {tags.map((tag, index) => (
              <span key={index} className="px-3 py-1 bg-[#F8FAF4] text-[#14B8A6] rounded-full text-sm">
                {tag.replace('_', ' ')}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Error Details (if validation failed) */}
      {!demoData.processing_success && demoData.rejection_reason && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-6">
          <div className="flex items-center mb-4">
            <div className="w-8 h-8 bg-red-100 rounded-lg flex items-center justify-center mr-3">
              <svg className="w-5 h-5" fill="none" stroke="#14B8A6" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-red-800">Processing Details</h2>
          </div>
          <p className="text-red-700">{demoData.rejection_reason}</p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex justify-center space-x-4 pt-6">
        <button 
          onClick={fetchDemoData}
          className="px-6 py-3 btn btn-primary text-white rounded-lg transition-colors"
        >
          Run Demo Again
        </button>
        <button 
          onClick={() => window.history.back()}
          className="px-6 py-3 btn btn-ghost text-gray-700 rounded-lg transition-colors"
        >
          Back to Home
        </button>
      </div>
    </div>
  );
};

export default DemoPage;