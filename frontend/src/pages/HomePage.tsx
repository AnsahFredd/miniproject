import React, { useEffect, useState } from "react";
import Button from "../components/ui/Button";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import toast from "react-hot-toast";
import ProcessingQueue from "../components/processing-queue/ProcessingQueue";
import UsageStatistics from "../components/usage-statistics/UsageStatistics";
import axios from "axios";
import homeBackground from "../assets/images/homebackground.jpg";
import { Clock, CheckCircle, AlertCircle, XCircle } from "lucide-react";

// Type definitions
interface Contract {
  id: string | number;
  name?: string;
  title?: string;
  expiry_date: string;
  days_until_expiry?: number;
}

interface Document {
  id: string | number;
  name?: string;
  title?: string;
  filename?: string;
  status: string;
  created_at?: string;
  updated_at?: string;
  upload_date?: string;
  file_size?: number;
  file_type?: string;
}

interface DocumentStats {
  totalDocuments: number;
  completedDocuments: number;
  processingDocuments: number;
  failedDocuments: number;
  recentUploads: Document[];
  averageProcessingTime: number;
}

interface ContractsData {
  expiringCount: number;
  contracts: Contract[];
  loading: boolean;
  error: string | null;
}

const API = import.meta.env.VITE_API_BASE_URL;

const HomePage = () => {
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [documentStats, setDocumentStats] = useState<DocumentStats>({
    totalDocuments: 0,
    completedDocuments: 0,
    processingDocuments: 0,
    failedDocuments: 0,
    recentUploads: [],
    averageProcessingTime: 0,
  });

  const [contractsData, setContractsData] = useState<ContractsData>({
    expiringCount: 0,
    contracts: [],
    loading: true,
    error: null,
  });
  const [statsLoading, setStatsLoading] = useState(true);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Helper function to safely handle status values
  const safeGetStatus = (status: string | undefined | null): string => {
    return (status || 'unknown').toLowerCase();
  };

  const headers = {
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  };

  // Function to handle document updates from ProcessingQueue
  const handleDocumentUpdate = () => {
    setRefreshTrigger(prev => prev + 1);
  };

  useEffect(() => {
    const fetchDocumentStats = async () => {
      try {
        setStatsLoading(true);

        if (!token) {
          console.log("No authentication token found");
          setStatsLoading(false);
          return;
        }

        console.log("[v0] Fetching documents from:", `${API}/documents/`);
        const res = await axios.get(`${API}/documents/`, { headers });

        console.log("[v0] API Response:", res.data);

        let docs: Document[] = [];
        if (res.data.data && Array.isArray(res.data.data)) {
          // Paginated response
          docs = res.data.data;
        } else if (Array.isArray(res.data)) {
          // Direct array response
          docs = res.data;
        } else {
          console.warn("[v0] Unexpected response format:", res.data);
          docs = [];
        }

        console.log("[v0] Processed documents:", docs);
        setDocuments(docs);

        const total = docs.length;
        const completed = docs.filter((d: any) => {
          const status = safeGetStatus(d.status);
          return status === "completed" || status === "complete" || status === "processed" || status === "ready";
        }).length;
        
        const processing = docs.filter((d: any) => {
          const status = safeGetStatus(d.status);
          return status === "processing" || status === "in_progress" || status === "analyzing";
        }).length;
        
        const failed = docs.filter((d: any) => {
          const status = safeGetStatus(d.status);
          return status === "failed" || status === "error";
        }).length;

        // Get only completed documents for recent uploads
        const completedDocs = docs.filter((d: any) => {
          const status = safeGetStatus(d.status);
          return status === "completed" || status === "complete" || status === "processed" || status === "ready";
        });

        setDocumentStats({
          totalDocuments: total,
          completedDocuments: completed,
          processingDocuments: processing,
          failedDocuments: failed,
          recentUploads: completedDocs.slice(0, 5),
          averageProcessingTime: 0,
        });
      } catch (error: any) {
        console.error("[v0] Error fetching document stats:", error);
        if (error.response?.status === 401) {
          toast.error("Authentication expired. Please log in again.");
          // Handle auth error - could logout user
        } else {
          toast.error("Failed to load documents. Please try again.");
        }
      } finally {
        setStatsLoading(false);
      }
    };

    fetchDocumentStats();
  }, [token, refreshTrigger]);

  useEffect(() => {
    const fetchExpiringContracts = async () => {
      if (!token) return;

      try {
        setContractsData(prev => ({ ...prev, loading: true, error: null }));
        
        const response = await axios.get('/api/contracts/expiring', {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          params: {
            days_ahead: 30
          }
        });

        setContractsData({
          expiringCount: response.data.count || 0,
          contracts: response.data.contracts || [],
          loading: false,
          error: null
        });
      } catch (error: any) {
        console.error('Error fetching expiring contracts:', error);
        setContractsData(prev => ({
          ...prev,
          loading: false,
          error: error.response?.data?.message || 'Failed to fetch contract data'
        }));
      }
    };
    fetchExpiringContracts();
  }, [token]);


  const getStatusIcon = (status: string | undefined | null) => {
    const safeStatus = safeGetStatus(status);
    switch (safeStatus) {
      case "completed":
      case "complete":
      case "processed":
      case "ready":
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case "processing":
      case "in_progress":
      case "analyzing":
        return <Clock className="w-5 h-5 text-blue-500" />;
      case "failed":
      case "error":
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
    }
  };

  const getStatusColor = (status: string | undefined | null): string => {
    const safeStatus = safeGetStatus(status);
    switch (safeStatus) {
      case "completed":
      case "complete":
      case "processed":
      case "ready":
        return "text-green-600 bg-green-100";
      case "processing":
      case "in_progress":
      case "analyzing":
        return "text-blue-600 bg-blue-100";
      case "failed":
      case "error":
        return "text-red-600 bg-red-100";
      default:
        return "text-yellow-600 bg-yellow-100";
    }
  };

  const handleDocumentClick = (doc: Document) => {
    const safeStatus = safeGetStatus(doc.status);
    if (safeStatus === "completed" || safeStatus === "complete" || safeStatus === "processed" || safeStatus === "ready") {
      navigate(`/document/${doc.id}/review`);
    } else {
      toast.error("Document is still processing or failed. Please wait for completion.");
    }
  };

  return (
    <div className="w-full min-h-screen bg-[var(--bg-soft)]">
      {/* Hero Section */}
      <div className="w-full bg-white">
        <div className="px-4 mx-auto max-w-7xl sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-5 gap-12 items-center min-h-[85vh] py-16">
            
            {/* Left Column - Content (60%) */}
            <div className="order-2 lg:order-1 lg:col-span-3">
              <div className="max-w-xl">
                <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold text-[var(--color-primary)] mb-6 leading-tight">
                  Welcome to <span className="text-[var(--color-accent)]">LawLens</span>
                </h1>
                
                <div className="mb-8">
                  <p className="text-lg text-[var(--color-secondary)] mb-4">
                    Your intelligent legal document management and analysis platform. 
                    Streamline your legal workflows with AI-powered insights and comprehensive document processing.
                  </p>
                  <p className="text-base text-[var(--color-secondary)]">
                    Welcome back, <span className="font-medium text-[var(--color-primary)]">{user?.full_name || user?.full_name || "User"}</span>! 
                    Ready to manage your legal documents efficiently.
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col gap-4 sm:flex-row">
                  <Button
                    label="Upload Document"
                    onClick={() => navigate("/document")}
                    otherStyles="btn btn-primary"
                  />
                  <Button
                    label="Search & QA"
                    onClick={() => navigate("/search")}
                    otherStyles="btn btn-outline-accent"
                  />
                </div>
              </div>
            </div>

            {/* Right Column - Image (40%) */}
            <div className="order-1 lg:order-2 lg:col-span-2">
              <div className="relative">
                <div className="overflow-hidden bg-gray-100 shadow-2xl rounded-2xl">
                  <img
                    src={homeBackground}
                    alt="Legal document management"
                    className="w-full h-[300px] lg:h-[350px] object-cover"
                  />
                </div>
                
                <div className="absolute w-24 h-24 bg-yellow-400 rounded-full -bottom-4 -left-4 opacity-20"></div>
                <div className="absolute w-16 h-16 bg-blue-500 rounded-full -top-4 -right-4 opacity-20"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scrollable Content Section */}
      <div className="relative w-full bg-white shadow-lg">
        <div className="max-w-6xl px-4 py-16 mx-auto">
          
          {/* Processing Queue Section with Side Content */}
          <div className="mb-12">
            <div className="grid items-start grid-cols-1 gap-8 lg:grid-cols-3">
              
              {/* Left Content - Processing Queue */}
              <div className="lg:col-span-2">
                <ProcessingQueue onDocumentUpdate={handleDocumentUpdate} />
              </div>
              
              {/* Right Content - Information Panel */}
              <div className="lg:col-span-1">
                <div className="p-6 bg-white border border-gray-200 rounded-lg shadow-sm">
                  <h3 className="text-xl font-semibold text-[var(--color-primary)] mb-4">
                    Document Processing
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-[var(--color-primary)] mb-2">Quick Stats</h4>
                      <div className="space-y-2 text-sm text-[var(--color-secondary)]">
                        <div className="flex justify-between">
                          <span>Total Documents:</span>
                          <span className="font-medium">{statsLoading ? "Loading..." : documentStats.totalDocuments}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Completed:</span>
                          <span className="font-medium">{statsLoading ? "Loading..." : documentStats.completedDocuments}</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Processing:</span>
                          <span className="font-medium">{statsLoading ? "Loading..." : documentStats.processingDocuments}</span>
                        </div>
                        {documentStats.failedDocuments > 0 && (
                          <div className="flex justify-between">
                            <span className="text-gray-600">Failed:</span>
                            <span className="font-medium text-red-500">{documentStats.failedDocuments}</span>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="pt-4 border-t">
                      <h4 className="font-medium text-[var(--color-primary)] mb-2">Processing Tips</h4>
                      <ul className="text-sm text-[var(--color-secondary)] space-y-1">
                        <li>• Documents typically process within 2-5 minutes</li>
                        <li>• PDF files are processed fastest</li>
                        <li>• Large files may take longer to analyze</li>
                        <li>• You'll be notified when processing completes</li>
                      </ul>
                    </div>
                    
                    <div className="pt-4 border-t">
                      <h4 className="font-medium text-[var(--color-primary)] mb-2">Need Help?</h4>
                      <p className="text-sm text-[var(--color-secondary)] mb-3">
                        Having issues with document processing or need assistance with your legal documents?
                      </p>
                      <a
                        href="mailto:ansahfredrick01@gmail.com?subject=Support%20Request&body=Hello%20LawLens%20Team,"
                        className="inline-block w-full text-center btn btn-secondary"
                      >
                        Contact Support
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>          
          {/* Usage Statistics Component */}
          {token && (
            <div className="mb-12">
              <UsageStatistics token={token} />
            </div>
          )}

          {/* Additional Content Sections */}
          <div className="py-16 text-center">
            <h2 className="text-3xl font-bold text-[var(--color-primary)] mb-4">
              Your Legal Document Management Hub
            </h2>
            <p className="text-lg text-[var(--color-secondary)] max-w-3xl mx-auto leading-relaxed">
              Track your document processing, view analytics, and get AI-powered recommendations 
              to optimize your legal workflows. Our comprehensive platform helps you stay organized 
              and make informed decisions.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HomePage;