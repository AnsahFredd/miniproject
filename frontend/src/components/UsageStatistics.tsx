import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

const API = import.meta.env.VITE_API_BASE_URL;

interface DailyUsage {
  date: string;
  count: number;
  dayName: string;
}

interface UsageStatisticsProps {
  token: string | null;
}

const UsageStatistics: React.FC<UsageStatisticsProps> = ({ token }) => {
  const [usageData, setUsageData] = useState<DailyUsage[]>([]);
  const [totalProcessed, setTotalProcessed] = useState<number>(0);
  const [percentageChange, setPercentageChange] = useState<number>(0);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const getLast7Days = (): DailyUsage[] => {
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const result: DailyUsage[] = [];
    for (let i = 6; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      const localDateString = `${year}-${month}-${day}`;
      result.push({
        date: localDateString,
        count: 0,
        dayName: days[date.getDay()],
      });
    }
    return result;
  };

  const getLocalDateString = (dateInput: any): string => {
    let date: Date;
    if (dateInput instanceof Date) {
      date = dateInput;
    } else if (typeof dateInput === 'string' || typeof dateInput === 'number') {
      date = new Date(dateInput);
    } else {
      return '';
    }
    if (isNaN(date.getTime())) return '';
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const fetchUsageStatistics = async () => {
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      if (!API) throw new Error('API URL not configured');
      const response = await axios.get(`${API}/documents/`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (Array.isArray(response.data)) {
        const documents = response.data;
        const last7Days = getLast7Days();
        const dailyCounts: { [key: string]: number } = {};
        let totalLast30Days = 0;
        let totalPrevious30Days = 0;

        const now = new Date();
        const thirtyDaysAgo = new Date(now.getTime() - 30 * 86400000);
        const sixtyDaysAgo = new Date(now.getTime() - 60 * 86400000);

        documents.forEach((doc: any) => {
          const dateValue = doc.upload_date || doc.created_at || doc.uploaded_at || doc.createdAt || doc.date || doc.timestamp;
          if (!dateValue) return;
          const localDateString = getLocalDateString(dateValue);
          if (!localDateString) return;
          const uploadDate = new Date(dateValue);
          if (uploadDate >= new Date(now.getTime() - 7 * 86400000)) {
            dailyCounts[localDateString] = (dailyCounts[localDateString] || 0) + 1;
          }
          if (uploadDate >= thirtyDaysAgo) {
            totalLast30Days++;
          } else if (uploadDate >= sixtyDaysAgo) {
            totalPrevious30Days++;
          }
        });

        const chartData = last7Days.map((day) => ({
          ...day,
          count: dailyCounts[day.date] || 0,
        }));

        const change = totalPrevious30Days > 0
          ? Math.round(((totalLast30Days - totalPrevious30Days) / totalPrevious30Days) * 100)
          : totalLast30Days > 0 ? 100 : 0;

        setUsageData(chartData);
        setTotalProcessed(totalLast30Days);
        setPercentageChange(change);
      } else {
        setUsageData(getLast7Days());
        setTotalProcessed(0);
        setPercentageChange(0);
      }
    } catch (err: any) {
      let errorMessage = 'Failed to load usage statistics';
      if (err.code === 'ECONNABORTED') errorMessage = 'Request timeout';
      else if (err.response?.status === 401) errorMessage = 'Unauthorized';
      else if (err.response?.status === 403) errorMessage = 'Forbidden';
      else if (err.response?.status >= 500) errorMessage = 'Server error';
      else if (!navigator.onLine) errorMessage = 'No internet connection';
      else if (err.message) errorMessage = err.message;
      setError(errorMessage);
      setUsageData(getLast7Days());
      setTotalProcessed(0);
      setPercentageChange(0);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUsageStatistics();
  }, [token]);

  if (!token) return null;

  return (
    <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6 mt-11 mx-11">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Usage</h2>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-gray-600">Loading usage data...</span>
        </div>
      ) : error ? (
        <div className="text-center py-8 text-red-600 text-sm">{error}</div>
      ) : (
        <>
          <div className="mb-8">
            <h3 className="text-sm font-medium text-gray-600 mb-3">Document Processing</h3>
            <div className="flex items-baseline gap-3">
              <span className="text-4xl font-bold text-gray-900">{totalProcessed}</span>
              <div className="flex items-baseline gap-2">
                <span className="text-sm text-gray-500">Last 30 Days</span>
                {percentageChange !== 0 && (
                  <span className={`text-sm font-semibold ${percentageChange > 0 ? 'text-emerald-500' : 'text-red-500'}`}>
                    {percentageChange > 0 ? '+' : ''}{percentageChange}%
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={usageData} margin={{ top: 10, right: 20, bottom: 30, left: 0 }}>
                <CartesianGrid strokeDasharray="2 2" />
                <XAxis dataKey="dayName" />
                <YAxis allowDecimals={false} />
                <Tooltip formatter={(value: number) => `${value} document${value !== 1 ? 's' : ''}`} />
                <Bar dataKey="count" fill="#8884d8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <p className="text-xs text-gray-400 text-center mt-4">
            Daily document processing over the last 7 days
          </p>
        </>
      )}
    </div>
  );
};

export default UsageStatistics;
