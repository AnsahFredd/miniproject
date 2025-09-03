// import React, { useState, useEffect } from 'react';
// import axios from 'axios';
// import {
//   BarChart,
//   Bar,
//   XAxis,
//   YAxis,
//   CartesianGrid,
//   Tooltip,
//   ResponsiveContainer,
//   PieChart,
//   Pie,
//   Cell,
// } from 'recharts';

// const API = import.meta.env.VITE_API_BASE_URL;

// interface DailyUsage {
//   date: string;
//   count: number;
//   dayName: string;
// }

// interface StatusData {
//   name: string;
//   value: number;
//   color: string;
// }

// interface UsageStatisticsProps {
//   token: string | null;
// }

// const UsageStatistics: React.FC<UsageStatisticsProps> = ({ token }) => {
//   const [usageData, setUsageData] = useState<DailyUsage[]>([]);
//   const [statusData, setStatusData] = useState<StatusData[]>([]);
//   const [totalProcessed, setTotalProcessed] = useState<number>(0);
//   const [percentageChange, setPercentageChange] = useState<number>(0);
//   const [isLoading, setIsLoading] = useState<boolean>(true);
//   const [error, setError] = useState<string | null>(null);

//   const getLast7Days = (): DailyUsage[] => {
//     const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
//     const result: DailyUsage[] = [];
//     for (let i = 6; i >= 0; i--) {
//       const date = new Date();
//       date.setDate(date.getDate() - i);
//       const year = date.getFullYear();
//       const month = String(date.getMonth() + 1).padStart(2, '0');
//       const day = String(date.getDate()).padStart(2, '0');
//       const localDateString = `${year}-${month}-${day}`;
//       result.push({
//         date: localDateString,
//         count: 0,
//         dayName: days[date.getDay()],
//       });
//     }
//     return result;
//   };

//   const getLocalDateString = (dateInput: any): string => {
//     let date: Date;
//     if (dateInput instanceof Date) {
//       date = dateInput;
//     } else if (typeof dateInput === 'string' || typeof dateInput === 'number') {
//       date = new Date(dateInput);
//     } else {
//       return '';
//     }
//     if (isNaN(date.getTime())) return '';
//     const year = date.getFullYear();
//     const month = String(date.getMonth() + 1).padStart(2, '0');
//     const day = String(date.getDate()).padStart(2, '0');
//     return `${year}-${month}-${day}`;
//   };

//   const mapApiStatusToDisplayStatus = (apiStatus: string): string => {
//     const status = apiStatus?.toLowerCase();
//     switch (status) {
//       case 'completed':
//       case 'complete':
//       case 'done':
//       case 'finished':
//       case 'processed':
//       case 'ready':
//       case 'success':
//       case 'successful':
//         return 'Completed';
//       case 'processing':
//       case 'in_progress':
//       case 'analyzing':
//         return 'Processing';
//       case 'failed':
//       case 'error':
//       case 'cancelled':
//       case 'canceled':
//         return 'Failed';
//       case 'uploaded':
//       case 'pending':
//         return 'Uploaded';
//       default:
//         return 'Other';
//     }
//   };

//   const fetchUsageStatistics = async () => {
//     if (!token) {
//       setIsLoading(false);
//       return;
//     }

//     try {
//       setIsLoading(true);
//       setError(null);
      
//       if (!API) throw new Error('API URL not configured');
      
//       const response = await axios.get(`${API}/documents/`, {
//         headers: {
//           Authorization: `Bearer ${token}`,
//           'Content-Type': 'application/json',
//         },
//       });

//       let documents: any[] = [];
//       if (response.data && Array.isArray(response.data.data)) {
//         // Paginated response
//         documents = response.data.data;
//       } else if (Array.isArray(response.data)) {
//         // Direct array response
//         documents = response.data;
//       } else {
//         console.warn('Unexpected response format:', response.data);
//         documents = [];
//       }

//       console.log('Documents received:', documents);

//       if (documents.length === 0) {
//         setUsageData(getLast7Days());
//         setStatusData([]);
//         setTotalProcessed(0);
//         setPercentageChange(0);
//         return;
//       }

//       const last7Days = getLast7Days();
//       const dailyCounts: { [key: string]: number } = {};
//       const statusCounts: { [key: string]: number } = {};
//       let totalLast30Days = 0;
//       let totalPrevious30Days = 0;

//       const now = new Date();
//       const thirtyDaysAgo = new Date(now.getTime() - 30 * 86400000);
//       const sixtyDaysAgo = new Date(now.getTime() - 60 * 86400000);

//       documents.forEach((doc: any) => {
//         // Get date from various possible fields
//         const dateValue = doc.upload_date || doc.created_at || doc.uploaded_at || doc.createdAt || doc.date || doc.timestamp;
        
//         if (dateValue) {
//           const localDateString = getLocalDateString(dateValue);
//           if (localDateString) {
//             const uploadDate = new Date(dateValue);
            
//             // Count for last 7 days chart
//             if (uploadDate >= new Date(now.getTime() - 7 * 86400000)) {
//               dailyCounts[localDateString] = (dailyCounts[localDateString] || 0) + 1;
//             }
            
//             // Count for percentage change calculation
//             if (uploadDate >= thirtyDaysAgo) {
//               totalLast30Days++;
//             } else if (uploadDate >= sixtyDaysAgo) {
//               totalPrevious30Days++;
//             }
//           }
//         }

//         // Count status distribution for all documents
//         const status = mapApiStatusToDisplayStatus(doc.status || doc.processing_status || doc.state);
//         statusCounts[status] = (statusCounts[status] || 0) + 1;
//       });

//       // Prepare chart data for daily usage
//       const chartData = last7Days.map((day) => ({
//         ...day,
//         count: dailyCounts[day.date] || 0,
//       }));

//       // Prepare status distribution data
//       const statusColors = {
//         'Completed': '#10B981',
//         'Processing': '#3B82F6',
//         'Failed': '#EF4444',
//         'Uploaded': '#F59E0B',
//         'Other': '#6B7280'
//       };

//       const statusChartData = Object.entries(statusCounts).map(([status, count]) => ({
//         name: status,
//         value: count,
//         color: statusColors[status as keyof typeof statusColors] || '#6B7280'
//       }));

//       // Calculate percentage change
//       const change = totalPrevious30Days > 0
//         ? Math.round(((totalLast30Days - totalPrevious30Days) / totalPrevious30Days) * 100)
//         : totalLast30Days > 0 ? 100 : 0;

//       setUsageData(chartData);
//       setStatusData(statusChartData);
//       setTotalProcessed(totalLast30Days);
//       setPercentageChange(change);

//     } catch (err: any) {
//       console.error('Error fetching usage statistics:', err);
//       let errorMessage = 'Failed to load usage statistics';
      
//       if (err.code === 'ECONNABORTED') {
//         errorMessage = 'Request timeout - please try again';
//       } else if (err.response?.status === 401) {
//         errorMessage = 'Session expired - please log in again';
//       } else if (err.response?.status === 403) {
//         errorMessage = 'Access denied';
//       } else if (err.response?.status >= 500) {
//         errorMessage = 'Server error - please try again later';
//       } else if (!navigator.onLine) {
//         errorMessage = 'No internet connection';
//       } else if (err.message && err.message !== 'Network Error') {
//         errorMessage = err.message;
//       }
      
//       setError(errorMessage);
//       setUsageData(getLast7Days());
//       setStatusData([]);
//       setTotalProcessed(0);
//       setPercentageChange(0);
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   useEffect(() => {
//     fetchUsageStatistics();
//   }, [token]);

//   if (!token) return null;

//   const CustomTooltip = ({ active, payload, label }: any) => {
//     if (active && payload && payload.length) {
//       return (
//         <div className="p-3 bg-white border border-gray-200 rounded-md shadow-lg">
//           <p className="font-medium text-gray-800">{label}</p>
//           <p className="text-sm text-gray-600">
//             {`${payload[0].value} document${payload[0].value !== 1 ? 's' : ''} uploaded`}
//           </p>
//         </div>
//       );
//     }
//     return null;
//   };

//   const PieTooltip = ({ active, payload }: any) => {
//     if (active && payload && payload.length) {
//       return (
//         <div className="p-2 bg-white border border-gray-200 rounded-md shadow-lg">
//           <p className="text-sm font-medium">{payload[0].name}</p>
//           <p className="text-sm text-gray-600">{payload[0].value} documents</p>
//         </div>
//       );
//     }
//     return null;
//   };

//   return (
//     <div className="space-y-6">
//       {/* Main Usage Statistics Card */}
//       <div className="p-6 bg-white border border-gray-200 rounded-lg shadow-lg card">
//         <div className="flex items-center justify-between mb-6">
//           <h2 className="text-lg font-semibold text-[var(--color-primary)]">Usage Statistics</h2>
//           <button
//             onClick={fetchUsageStatistics}
//             className="text-xs btn btn-ghost"
//             disabled={isLoading}
//           >
//             {isLoading ? 'Refreshing...' : 'Refresh'}
//           </button>
//         </div>

//         {isLoading ? (
//           <div className="flex items-center justify-center h-48" role="status" aria-live="polite">
//             <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-accent)]"></div>
//             <span className="ml-3 text-[var(--color-secondary)]">Loading usage data...</span>
//           </div>
//         ) : error ? (
//           <div className="text-center py-8 text-[var(--color-primary)] text-sm bg-[var(--bg-soft)] rounded-md border border-gray-200" role="alert" aria-live="assertive">
//             <div className="mb-2">⚠️</div>
//             <div>{error}</div>
//             <button
//               onClick={fetchUsageStatistics}
//               className="mt-3 text-xs btn btn-outline-accent"
//             >
//               Try Again
//             </button>
//           </div>
//         ) : (
//           <>
//             {/* Statistics Summary */}
//             <div className="grid grid-cols-1 gap-6 mb-8 md:grid-cols-2">
//               <div className="text-center">
//                 <h3 className="text-sm font-medium text-[var(--color-secondary)] mb-2">Documents (30 Days)</h3>
//                 <div className="flex items-center justify-center gap-2">
//                   <span className="text-3xl font-bold text-[var(--color-accent)]">{totalProcessed}</span>
//                   {percentageChange !== 0 && (
//                     <span className={`text-sm font-semibold ${
//                       percentageChange > 0 ? 'text-green-600' : 'text-red-600'
//                     }`}>
//                       {percentageChange > 0 ? '+' : ''}{percentageChange}%
//                     </span>
//                   )}
//                 </div>
//               </div>
              
//               <div className="text-center">
//                 <h3 className="text-sm font-medium text-[var(--color-secondary)] mb-2">Total Documents</h3>
//                 <span className="text-3xl font-bold text-[var(--color-primary)]">
//                   {statusData.reduce((sum, item) => sum + item.value, 0)}
//                 </span>
//               </div>
//             </div>

//             <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
//               {/* Daily Upload Chart */}
//               <div className="lg:col-span-2">
//                 <h3 className="text-sm font-medium text-[var(--color-secondary)] mb-4">Daily Uploads (Last 7 Days)</h3>
//                 <div className="h-64 p-4 bg-white border border-gray-100 rounded-md">
//                   <ResponsiveContainer width="100%" height="100%">
//                     <BarChart data={usageData} margin={{ top: 10, right: 20, bottom: 30, left: 0 }}>
//                       <CartesianGrid stroke="#F3F4F6" strokeDasharray="3 3" />
//                       <XAxis 
//                         dataKey="dayName" 
//                         tick={{ fill: '#64748B', fontSize: 12 }}
//                         axisLine={{ stroke: '#E5E7EB' }}
//                         tickLine={{ stroke: '#E5E7EB' }}
//                       />
//                       <YAxis 
//                         allowDecimals={false} 
//                         tick={{ fill: '#64748B', fontSize: 12 }}
//                         axisLine={{ stroke: '#E5E7EB' }}
//                         tickLine={{ stroke: '#E5E7EB' }}
//                       />
//                       <Tooltip content={<CustomTooltip />} />
//                       <Bar 
//                         dataKey="count" 
//                         fill="#14B8A6" 
//                         radius={[4, 4, 0, 0]}
//                         stroke="#0FA596"
//                         strokeWidth={1}
//                       />
//                     </BarChart>
//                   </ResponsiveContainer>
//                 </div>
//               </div>
//             </div>

//             <p className="text-xs text-[var(--color-secondary)] text-center mt-6">
//               Statistics are updated in real-time and show your document processing activity
//             </p>
//           </>
//         )}
//       </div>
//     </div>
//   );
// };

// export default UsageStatistics;