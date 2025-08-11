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
    <div className="max-w-4xl mx-auto p-4 sm:p-6 bg-white">
      <div className="mb-6 sm:mb-8">
        <div className="relative mb-4">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-[var(--color-secondary)] w-5 h-5" />
          <input
            type="text"
            placeholder="Search legal documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="w-full input h-12 pl-10 pr-4"
          />
        </div>

        <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 mb-4">
          {filters.map(({ id, label, value, setter, options }) => (
            <div className="relative w-full sm:w-auto" key={id}>
              <select
                aria-label={label}
                value={value}
                onChange={(e) => setter(e.target.value)}
                className="w-full appearance-none bg-white border border-gray-300 rounded-lg px-4 py-2 pr-8 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]"
              >
                <option value="">All Types</option>
                {options.map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-2 top-1/2 transform -translate-y-1/2 w-4 h-4 text-[var(--color-secondary)] pointer-events-none" />
            </div>
          ))}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 sm:p-4 bg-red-50 border border-red-200 rounded-lg text-red-700" role="alert" aria-live="assertive">
          {error}
        </div>
      )}

      <div className="mb-6 sm:mb-8">
        <h2 className="text-lg sm:text-xl font-semibold text-[var(--color-primary)] mb-4">Search Results</h2>
        {loading ? (
          <div className="text-center py-8" role="status" aria-live="polite">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-accent)] mx-auto"></div>
            <p className="mt-2 text-[var(--color-secondary)]">Searching...</p>
          </div>
        ) : searchResults.length === 0 && searchQuery.trim() ? (
          <div className="text-center py-8 text-[var(--color-secondary)]">
            <p className="text-sm sm:text-base px-4">No search results found. Try adjusting your search terms or filters.</p>
          </div>
        ) : searchResults.length === 0 ? (
          <div className="text-center py-8 text-[var(--color-secondary)]">
            <p className="text-sm sm:text-base px-4">Enter a search query to find legal documents.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {searchResults.map((result) => (
              <div key={result.id} className="border border-gray-200 rounded-lg p-3 sm:p-4 hover:shadow-md transition-shadow">
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-2">
                  <div className="flex items-start gap-3 flex-1">
                    <FileText className="w-5 h-5 text-[var(--color-secondary)] mt-1 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-[var(--color-primary)] break-words">{result.title}</h3>
                      <p className="text-sm text-[var(--color-secondary)] mb-2 break-words">{result.section}</p>
                      <p
                        className="text-sm text-[var(--color-secondary)] break-words"
                        dangerouslySetInnerHTML={{ __html: highlightMatch(result.description, searchQuery) }}
                      />
                    </div>
                  </div>
                  <span className="text-sm font-medium badge badge-accent mt-2 sm:mt-0 self-start" aria-label={`Similarity score ${(result.similarity_score * 100).toFixed(1)} percent`}>
                    {(result.similarity_score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div>
        <h2 className="text-lg sm:text-xl font-semibold text-[var(--color-primary)] mb-4">Question Answering</h2>
        <div className="border border-gray-200 rounded-lg p-3 sm:p-4">
          <div className="mb-4">
            <input
              type="text"
              placeholder="Type your question here..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleQuestionSubmit()}
              className="w-full input mb-3"
            />
            <button
              onClick={handleQuestionSubmit}
              disabled={questionLoading || !question.trim()}
              className="w-full sm:w-auto btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {questionLoading ? 'Processing...' : 'Ask Question'}
            </button>
          </div>

          {answer && (
            <div className="mt-4 p-3 sm:p-4 card">
              <p className="font-medium text-[var(--color-primary)] mb-2">Answer:</p>
              <p className="text-[var(--color-secondary)] break-words">{answer}</p>
              <p className="text-sm text-[var(--color-secondary)] mt-2">Source: Based on search results</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LegalDocumentSearch;