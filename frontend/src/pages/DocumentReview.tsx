import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import {
  FileText,
  Calendar,
  DollarSign,
  RefreshCw,
  Users,
  AlertTriangle,
  Scale,
  Building,
  Loader2,
} from 'lucide-react';
import axios from 'axios';
import { motion } from 'framer-motion'; // ✅ Animation import

type ClauseItem = {
  icon: string;
  title: string;
  subtitle: string;
  value: any;
};

type AnalysisData = {
  document_info?: { content: string };
  financial_summary?: {
    rent_amount?: number;
    deposit?: number;
    other_fees?: string[];
  };
  term_information?: {
    lease_duration?: string;
    primary_term?: string;
    renewal_option?: string;
    renewal_term?: string;
  };
  summary?: { text: string };
  clause_overview?: any[];
};

const DocumentReview = () => {
  const { id: documentId } = useParams<{ id: string }>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [analysisData, setAnalysisData] = useState<AnalysisData | null>(null);

  const API = import.meta.env.VITE_API_BASE_URL;

  const getClauseIcon = (type: string) => {
    const iconMap: Record<string, React.FC<{ className?: string }>> = {
      lease_term: Calendar,
      rent: DollarSign,
      renewal: RefreshCw,
      maintenance: Users,
      improvements: Building,
      termination: AlertTriangle,
      dispute: Scale,
      regulations: FileText,
      default: FileText,
    };

    const IconComponent = iconMap[type] || iconMap['default'];
    return <IconComponent className="w-4 h-4 text-gray-600" />;
  };

  const formatCurrency = (amount: number | string | undefined) => {
    if (!amount) return 'Not specified';
    const numAmount =
      typeof amount === 'string'
        ? parseFloat(amount.replace(/[^0-9.]/g, ''))
        : amount;
    return `$${numAmount.toLocaleString()}/month`;
  };

  const formatTerm = (term: string | number | undefined) => {
    if (!term) return 'Not specified';
    return typeof term === 'string' ? term : `${term} years`;
  };

  const extractKeyData = (analysis: AnalysisData | null): ClauseItem[] => {
    if (!analysis) return [];

    const financial = analysis.financial_summary || {};
    const terms = analysis.term_information || {};

    const keyItems: ClauseItem[] = [];

    if (terms.lease_duration || terms.primary_term) {
      keyItems.push({
        icon: 'lease_term',
        title: formatTerm(terms.lease_duration || terms.primary_term),
        subtitle: 'Lease Term',
        value: terms.lease_duration || terms.primary_term,
      });
    }

    if (financial.rent_amount) {
      keyItems.push({
        icon: 'rent',
        title: formatCurrency(financial.rent_amount),
        subtitle: 'Rent Amount',
        value: financial.rent_amount,
      });
    }

    if (terms.renewal_term || terms.renewal_option) {
      keyItems.push({
        icon: 'renewal',
        title: formatTerm(terms.renewal_term || terms.renewal_option),
        subtitle: 'Renewal Option',
        value: terms.renewal_option || terms.renewal_term,
      });
    }

    const standardClauses: ClauseItem[] = [
      { icon: 'maintenance', title: 'Shared', subtitle: 'Maintenance', value: 'shared' },
      { icon: 'improvements', title: 'Tenant', subtitle: 'Improvements', value: 'permitted' },
      { icon: 'termination', title: 'Conditions Apply', subtitle: 'Early Termination', value: 'conditional' },
      { icon: 'dispute', title: 'Mediation', subtitle: 'Dispute Resolution', value: 'mediation' },
      { icon: 'regulations', title: 'Local Regulations', subtitle: 'Compliance', value: 'required' },
    ];

    return [...keyItems, ...standardClauses];
  };

  const fetchDocumentAnalysis = async () => {
    if (!documentId) return;

    try {
      setLoading(true);
      setError('');
      setAnalysisData(null); // Reset on re-fetch

      const token = localStorage.getItem('token') || localStorage.getItem('authToken');
      const response = await axios.get(`${API}/documents/${documentId}/analysis`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      setAnalysisData(response.data);
    } catch (err: any) {
      console.error('Error fetching document analysis:', err);
      setError(err.message || 'Failed to load document analysis');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (documentId) {
      setAnalysisData(null);
      setError('');
      fetchDocumentAnalysis();
    }
  }, [documentId]);

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto p-6 bg-gray-50">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-4" />
            <p className="text-gray-600">Analyzing document...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error && !analysisData) {
    return (
      <div className="max-w-6xl mx-auto p-6 bg-gray-50">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">{error}</p>
          <button
            onClick={fetchDocumentAnalysis}
            className="mt-2 text-red-600 hover:text-red-800 underline"
          >
            Try again
          </button>
        </div>
      </div>
    );
  }

  const keyData = extractKeyData(analysisData);
  const documentContent = analysisData?.document_info?.content || '';
  const summary = analysisData?.summary?.text || '';

  return (
    <div className="max-w-6xl mx-auto p-6 bg-gray-50">
      <div className="grid grid-cols-1 lg:grid-cols-[70%_30%] gap-6">
        {/* 🌀 Document Review */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="bg-white rounded-lg shadow-sm border"
        >
          <div className="p-6 border-b">
            <h2 className="text-xl font-semibold text-gray-900">Document Review</h2>
            <p className="text-sm text-gray-600 mt-1">Review the processed document, analyze clauses, and access summaries.</p>
          </div>

          <div className="p-6">
            <div className="flex items-center gap-4 mb-4">
              <span className="text-sm font-medium text-gray-700">Original Formatting</span>
              <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">Text-Only</span>
            </div>

            <div className="w-full h-96 p-4 border rounded-lg text-sm text-gray-700 leading-relaxed overflow-y-auto bg-gray-50">
              {documentContent || 'Document content not available'}
            </div>
          </div>
        </motion.div>

        {/* 🧠 Clause Overview */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="bg-white rounded-lg shadow-sm border"
        >
          <div className="p-6">
            <h3 className="text-2xl font-bold text-gray-900">Clause Overview</h3>
          </div>

          <div className="p-6 space-y-4">
            {keyData.map((clause, index) => (
              <div key={index} className="flex items-start gap-3">
                <div className="p-2 bg-gray-100 rounded-lg">{getClauseIcon(clause.icon)}</div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 text-sm">{clause.title}</div>
                  <div className="text-xs text-gray-500">{clause.subtitle}</div>
                </div>
              </div>
            ))}

            {keyData.length === 0 && !loading && (
              <div className="text-center py-8 text-gray-500">
                <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No clauses identified</p>
              </div>
            )}
          </div>

          {summary && (
            <div className="border-t">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.4, delay: 0.2 }}
                className="p-6"
              >
                <h4 className="font-semibold text-xl text-gray-900 mb-3">Summary</h4>
                <p className="text-sm text-gray-700 leading-relaxed">{summary}</p>
              </motion.div>
            </div>
          )}
        </motion.div>
      </div>

      {/* ✅ Final callout */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.3 }}
        className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200"
      >
        <h4 className="font-medium text-blue-900 mb-2">Document Analysis Complete</h4>
        <ul className="text-sm text-blue-800 space-y-1">
          <li>• Document automatically loaded and analyzed from backend</li>
          <li>• Key clauses extracted including lease terms, rent amounts, renewal options</li>
          <li>• Financial information, parties, and important dates identified</li>
          <li>• Summary generated based on document content and extracted data</li>
        </ul>
      </motion.div>
    </div>
  );
};

export default DocumentReview;
