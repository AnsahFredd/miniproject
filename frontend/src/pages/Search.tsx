import React, { useState, useEffect } from 'react';
import { Search, FileText, ChevronDown } from 'lucide-react';
import axios from 'axios';
import { useAuth } from "../auth/AuthContext";

interface SearchResult {
  id: string | number;
  title: string;
  section: string;
  description: string;
  similarity_score: number;
}

const API = import.meta.env.VITE_API_BASE_URL;

const LegalDocumentSearch = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [documentType, setDocumentType] = useState('');
  const [legalDomain, setLegalDomain] = useState('');
  const [dateRange, setDateRange] = useState('');
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);
  const [questionLoading, setQuestionLoading] = useState(false);
  const [error, setError] = useState("");

  const { token, logout } = useAuth();

  const highlightMatch = (text: string, query: string) => {
    if (!query) return text;
    const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(${escapedQuery})`, 'gi');
    return text.replace(regex, '<mark>$1</mark>');
  };

  const filters = [
    { id: 'document-type', label: "Document Type", value: documentType, setter: setDocumentType, options: ["Contract", "Agreement", "Policy"] },
    { id: 'legal-domain', label: "Legal Domain", value: legalDomain, setter: setLegalDomain, options: ["Property Law", "Employment Law", "Contract Law"] },
    { id: 'date-range', label: "Date Range", value: dateRange, setter: setDateRange, options: ["Last 7 days", "Last 30 days", "Last 6 months", "Last year"] }
  ];

  const searchDocuments = async (
    query: string,
    filters: { documentType: string; legalDomain: string; dateRange: string }
  ) => {
    setLoading(true);
    setError("");

    try {
      const response = await axios.post(
        `${API}/search/`,
        {
          query,
          documentType: filters.documentType,
          legalDomain: filters.legalDomain,
          dateRange: filters.dateRange,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
          withCredentials: true
        }
      );

      const results = (response.data.results || []).map((doc: any, index: number) => ({
        id: doc.id || doc._id || `result-${index}`,
        title: doc.title || 'Untitled Document',
        section: doc.section || 'No Section',
        description: doc.description || 'No description available',
        similarity_score: doc.similarity_score || 0,
      }));

      setSearchResults(results);
    } catch (err) {
      console.error('Search failed:', err);
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        logout();
      }
      setError("Search failed. Please try again.");
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const askQuestion = async (question: string) => {
    if (!question.trim()) return;

    setQuestionLoading(true);
    setError("");
    
    try {
      const response = await axios.post(
        `${API}/questions/ask`,
        {
          question,
          context: searchResults,
        },
        {
          headers: { Authorization: `Bearer ${token}` },
          withCredentials: true,
        }
      );

      setAnswer(response.data.answer || 'No answer found.');
    } catch (err) {
      console.error('Question answering failed:', err);
      if (axios.isAxiosError(err) && err.response?.status === 401) {
        logout();
      }
      setError("Could not process your question. Please try again.");
      setAnswer('Sorry, I could not process your question at this time.');
    } finally {
      setQuestionLoading(false);
    }
  };

  const handleSearch = () => {
    if (!searchQuery.trim()) return;
    searchDocuments(searchQuery, { documentType, legalDomain, dateRange });
  };

  const handleQuestionSubmit = () => {
    askQuestion(question);
  };

  useEffect(() => {
    if (searchQuery.trim()) {
      const timeoutId = setTimeout(() => {
        handleSearch();
      }, 500);
      return () => clearTimeout(timeoutId);
    } else {
      setSearchResults([]);
    }
  }, [searchQuery, documentType, legalDomain, dateRange]);

  return (
    <div className="max-w-4xl mx-auto p-6 bg-white">
      <div className="mb-8">
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search legal documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div className="flex gap-4 mb-4">
          {filters.map(({ id, label, value, setter, options }) => (
            <div className="relative" key={id}>
              <select
                value={value}
                onChange={(e) => setter(e.target.value)}
                className="appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Types</option>
                {options.map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
            </div>
          ))}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}

      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Search Results</h2>
        {loading ? (
          <div className="text-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Searching...</p>
          </div>
        ) : searchResults.length === 0 && searchQuery.trim() ? (
          <div className="text-center py-8 text-gray-500">
            <p>No search results found. Try adjusting your search terms or filters.</p>
          </div>
        ) : searchResults.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <p>Enter a search query to find legal documents.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {searchResults.map((result) => (
              <div key={result.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-start gap-3">
                    <FileText className="w-5 h-5 text-gray-400 mt-1 flex-shrink-0" />
                    <div>
                      <h3 className="font-medium text-gray-900">{result.title}</h3>
                      <p className="text-sm text-gray-600 mb-2">{result.section}</p>
                      <p
                        className="text-sm text-gray-700"
                        dangerouslySetInnerHTML={{ __html: highlightMatch(result.description, searchQuery) }}
                      />
                    </div>
                  </div>
                  <span className="text-sm font-medium text-blue-600 bg-blue-50 px-2 py-1 rounded">
                    {(result.similarity_score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4">Question Answering</h2>
        <div className="border border-gray-200 rounded-lg p-4">
          <div className="mb-4">
            <input
              type="text"
              placeholder="Type your question here..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleQuestionSubmit()}
              className="w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              onClick={handleQuestionSubmit}
              disabled={questionLoading || !question.trim()}
              className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {questionLoading ? 'Processing...' : 'Ask Question'}
            </button>
          </div>

          {answer && (
            <div className="mt-4 p-4 bg-gray-50 rounded-lg">
              <p className="font-medium text-gray-900 mb-2">Answer:</p>
              <p className="text-gray-700">{answer}</p>
              <p className="text-sm text-gray-500 mt-2">Source: Based on search results</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LegalDocumentSearch;
