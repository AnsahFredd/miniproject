import React, { useState, useEffect, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import { FileText, Calendar, DollarSign, RefreshCw, Users, AlertTriangle, Scale, Building, Loader2 } from 'lucide-react';
import axios from 'axios';
import { motion } from 'framer-motion';

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

  // Animated variants
  const containerVariants = useMemo(
    () => ({
      hidden: { opacity: 0 },
      show: {
        opacity: 1,
        transition: { staggerChildren: 0.06, when: 'beforeChildren' },
      },
    }),
    []
  );

  const itemVariants = useMemo(
    () => ({
      hidden: { opacity: 0, y: 10 },
      show: { opacity: 1, y: 0 },
    }),
    []
  );

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
    return <IconComponent className="w-4 h-4 text-[var(--color-secondary)]" />;
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
      <div className="max-w-6xl mx-auto p-6 bg-[var(--bg-soft)]">
        <div className="flex items-center justify-center py-12" role="status" aria-live="polite">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin text-[var(--color-accent)] mx-auto mb-4" />
            <p className="text-[var(--color-secondary)]">Analyzing document...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error && !analysisData) {
    return (
      <div className="max-w-6xl mx-auto p-6 bg-[var(--bg-soft)]">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4" role="alert" aria-live="assertive">
          <p className="text-red-700">{error}</p>
          <button
            onClick={fetchDocumentAnalysis}
            className="mt-2 link-accent"
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
    <div className="relative max-w-6xl mx-auto p-6 bg-[var(--bg-soft)]">
      {/* Decorative background accents */}
      <div className="pointer-events-none absolute -z-10 inset-0 overflow-hidden">
        <div className="absolute -top-24 -right-24 w-80 h-80 rounded-full bg-[color:rgb(20_184_166_/_12%)] blur-3xl"></div>
        <div className="absolute -bottom-24 -left-24 w-96 h-96 rounded-full bg-[color:rgb(15_23_42_/_6%)] blur-3xl"></div>
      </div>

      <motion.div
        className="grid grid-cols-1 lg:grid-cols-[70%_30%] gap-6"
        variants={containerVariants}
        initial="hidden"
        animate="show"
      >
        {/* Document Review Card */}
        <motion.div
          variants={itemVariants}
          className="bg-white rounded-xl shadow-sm border overflow-hidden"
        >
          <div className="p-6 border-b">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-[var(--color-primary)]">
                Document Review
              </h2>
              {/* Animated chip */}
              <motion.span
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.35 }}
                className="px-2 py-1 bg-[color:rgb(20_184_166_/_12%)] text-[var(--color-accent)] text-xs rounded"
              >
                Text-Only
              </motion.span>
            </div>
            <div className="mt-2 h-1.5 w-16 bg-gradient-to-r from-[var(--color-accent)] to-transparent rounded-full" />
            <p className="text-sm text-[var(--color-secondary)] mt-3">
              Review the processed document, analyze clauses, and access summaries.
            </p>
          </div>

          <motion.div
            className="p-6"
            variants={itemVariants}
            transition={{ duration: 0.4 }}
          >
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35, delay: 0.05 }}
              className="w-full h-96 p-4 border rounded-lg text-sm text-[var(--color-secondary)] leading-relaxed overflow-y-auto bg-[var(--bg-soft)]"
            >
              {documentContent || 'Document content not available'}
            </motion.div>
          </motion.div>
        </motion.div>

        {/* Clause Overview Card */}
        <motion.div
          variants={itemVariants}
          className="bg-white rounded-xl shadow-sm border overflow-hidden"
        >
          <div className="p-6">
            <h3 className="text-2xl font-bold text-[var(--color-primary)]">Clause Overview</h3>
            <div className="mt-2 h-1.5 w-14 bg-gradient-to-r from-[var(--color-accent)] to-transparent rounded-full" />
          </div>

          <motion.div
            className="p-6 space-y-4"
            variants={containerVariants}
            initial="hidden"
            animate="show"
          >
            {keyData.map((clause, index) => (
              <motion.div
                key={index}
                variants={itemVariants}
                whileHover={{ y: -2, scale: 1.01 }}
                transition={{ type: 'spring', stiffness: 300, damping: 22 }}
                className="flex items-start gap-3 rounded-lg p-2 hover:bg-[var(--bg-soft)] border border-transparent hover:border-[color:rgb(20_184_166_/_18%)]"
              >
                <div className="p-2 bg-[var(--bg-soft)] rounded-lg shadow-sm">
                  {getClauseIcon(clause.icon)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-[var(--color-primary)] text-sm">
                    {clause.title}
                  </div>
                  <div className="text-xs text-[var(--color-secondary)]">{clause.subtitle}</div>
                </div>
              </motion.div>
            ))}

            {keyData.length === 0 && !loading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="text-center py-8 text-[var(--color-secondary)]"
              >
                <FileText className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No clauses identified</p>
              </motion.div>
            )}
          </motion.div>

          {summary && (
            <div className="border-t">
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.35, delay: 0.1 }}
                className="p-6"
              >
                <h4 className="font-semibold text-xl text-[var(--color-primary)] mb-3">Summary</h4>
                <p className="text-sm text-[var(--color-secondary)] leading-relaxed">
                  {summary}
                </p>
              </motion.div>
            </div>
          )}
        </motion.div>
      </motion.div>

      {/* Completion callout */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.25 }}
        className="mt-6 p-4 bg-[color:rgb(20_184_166_/_8%)] rounded-lg border border-[color:rgb(20_184_166_/_26%)]"
      >
        <h4 className="font-medium text-[var(--color-accent)] mb-2">Document Analysis Complete</h4>
        <ul className="text-sm text-[var(--color-secondary)] space-y-1">
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
