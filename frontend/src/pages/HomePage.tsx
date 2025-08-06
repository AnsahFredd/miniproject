import React, { useEffect, useState } from "react";
import Button from "../components/ui/Button";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import toast from "react-hot-toast";
import ProcessingQueue from "../components/ProcessingQueue";
import UsageStatistics from "../components/UsageStatistics";
import axios from "axios";
import AIRecommendations from "../components/Recommendation";

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

  // Fetch expiring contracts data
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
            days_ahead: 30 // Get contracts expiring in next 30 days
          }
        });

        setContractsData({
          expiringCount: response.data.count || 0,
          contracts: response.data.contracts || [],
          loading: false,
          error: null
        });
      } catch (error) {
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
    <div className="container mx-auto w-full min-h-screen px-4 pt-10 pb-6 text-[#121417] bg-[#FAFAFA]">
      {/* Heading */}
      <div className="flex flex-col gap-2 mb-6">
        <h1 className="text-3xl md:text-4xl font-bold">Dashboard</h1>
        <p className="text-[#61758A] text-base md:text-lg">
          Welcome back,{" "}
          <span className="font-medium">{user?.full_name || "User"}</span>! Here’s a quick overview of your recent activity and tools you might need.
        </p>
      </div>
      
      <ProcessingQueue />

      {/* AI Recommendations Component */}
      {token && <AIRecommendations token={token} />}  
      

      {/* Usage Statistics Component */}
      {token && (
        <div className="mb-8">
          <UsageStatistics token={token} />
        </div>
      )}
      <div className="flex flex-col lg:flex-row items-center mx-12 space-y-6 lg:space-y-0 lg:mx-0">
      <div className="w-full sm:w-[250px] mx-11">
          <Button
            label="Upload New Document"
            onClick={() => navigate("/document")}
            otherStyles="w-full bg-[#0D80F2] text-white py-2 px-4 rounded-lg hover:bg-[#006ad4] transition"
          />
        </div>

        <div className="w-full sm:w-[250px]">
          <Button
            label="Go to Search & QA"
            onClick={() => navigate("/search")}
            otherStyles="w-full bg-[#F0F2F5] text-[#121417] py-2 px-4 rounded-lg hover:bg-[#e4e7eb] transition"
          />
        </div>
        </div>
    </div>
  );
};

export default HomePage;
