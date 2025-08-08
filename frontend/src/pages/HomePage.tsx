import React, { useEffect, useState } from "react";
import Button from "../components/ui/Button";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import toast from "react-hot-toast";
import ProcessingQueue from "../components/ProcessingQueue";
import UsageStatistics from "../components/UsageStatistics";
import axios from "axios";
import AIRecommendations from "../components/Recommendation";
import homeBackground from "../assets/images/homebackground.jpg"

// Type definitions
interface Contract {
  id: string | number;
  name?: string;
  title?: string;
  expiry_date: string;
  days_until_expiry?: number;
}

interface ContractsData {
  expiringCount: number;
  contracts: Contract[];
  loading: boolean;
  error: string | null;
}

const HomePage = () => {
  const navigate = useNavigate();
  const { logout, token, user } = useAuth();

  const [contractsData, setContractsData] = useState<ContractsData>({
    expiringCount: 0,
    contracts: [],
    loading: true,
    error: null
  });

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

  return (
    <div className="w-full min-h-screen bg-[var(--bg-soft)]">
      {/* Hero Section */}
      <div className="w-full bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
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
                    Welcome back, <span className="font-medium text-[var(--color-primary)]">{user?.full_name || "User"}</span>! 
                    Ready to manage your legal documents efficiently.
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-4">
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
                <div className="rounded-2xl overflow-hidden shadow-2xl bg-gray-100">
                  <img
                    src={homeBackground || "/placeholder.svg"}
                    alt="Legal document management"
                    className="w-full h-[300px] lg:h-[350px] object-cover"
                  />
                </div>
                
                <div className="absolute -bottom-4 -left-4 w-24 h-24 bg-yellow-400 rounded-full opacity-20"></div>
                <div className="absolute -top-4 -right-4 w-16 h-16 bg-blue-500 rounded-full opacity-20"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scrollable Content Section */}
      <div className="relative w-full bg-white shadow-lg">
        <div className="max-w-6xl mx-auto px-4 py-16">
          
          {/* Processing Queue Section with Side Content */}
          <div className="mb-12">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
              
              {/* Left Content - Processing Queue */}
              <div className="lg:col-span-2">
                <ProcessingQueue />
              </div>
              
              {/* Right Content - Information Panel */}
              <div className="lg:col-span-1">
                <div className="bg-white border border-gray-200 rounded-lg p-6 shadow-sm">
                  <h3 className="text-xl font-semibold text-[var(--color-primary)] mb-4">
                    Document Processing
                  </h3>
                  
                  <div className="space-y-4">
                    <div>
                      <h4 className="font-medium text-[var(--color-primary)] mb-2">Quick Stats</h4>
                      <div className="space-y-2 text-sm text-[var(--color-secondary)]">
                        <div className="flex justify-between">
                          <span>Total Documents:</span>
                          <span className="font-medium">12</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Completed:</span>
                          <span className="font-medium">10</span>
                        </div>
                        <div className="flex justify-between">
                          <span>Processing:</span>
                          <span className="font-medium">2</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="border-t pt-4">
                      <h4 className="font-medium text-[var(--color-primary)] mb-2">Processing Tips</h4>
                      <ul className="text-sm text-[var(--color-secondary)] space-y-1">
                        <li>• Documents typically process within 2-5 minutes</li>
                        <li>• PDF files are processed fastest</li>
                        <li>• Large files may take longer to analyze</li>
                        <li>• You'll be notified when processing completes</li>
                      </ul>
                    </div>
                    
                    <div className="border-t pt-4">
                      <h4 className="font-medium text-[var(--color-primary)] mb-2">Need Help?</h4>
                      <p className="text-sm text-[var(--color-secondary)] mb-3">
                        Having issues with document processing or need assistance with your legal documents?
                      </p>
                      <button className="w-full btn btn-secondary">
                        Contact Support
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* AI Recommendations Component */}
          {token && (
            <div className="mb-12">
              <AIRecommendations token={token} />
            </div>
          )}

          {/* Usage Statistics Component */}
          {token && (
            <div className="mb-12">
              <UsageStatistics token={token} />
            </div>
          )}

          {/* Additional Content Sections */}
          <div className="text-center py-16">
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
