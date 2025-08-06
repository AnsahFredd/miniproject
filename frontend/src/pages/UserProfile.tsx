import React, { useState, useEffect } from 'react';
import { User, Mail, Calendar, FileText, MessageSquare, HelpCircle, RotateCcw, Lock, Folder, LogOut, Bell, Activity } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../auth/AuthContext';
import ProfileImageUpload from '../components/ProfileIageUpload';
import  { useNavigate } from "react-router-dom"

interface UserData {
  name: string;
  email: string;
  role: string;
  lastLogin: string;
}

interface ActivityStats {
  documentsUploaded: number;
  contractsAnalyzed: number;
  questionsAnswered: number;
}

interface Notification {
  id: string;
  message: string;
  type: 'warning' | 'info' | 'success';
  createdAt: string;
}

interface RecentActivity {
  id: string;
  action: string;
  fileName: string;
  timestamp: string;
}

interface AIAssistantSummary {
  weeklyQuestions: number;
  documentsThisWeek: number;
  mostActiveDay: string;
  contractReviews: number;
}

const API = import.meta.env.VITE_API_BASE_URL;


const UserProfile = () => {

  const [userData, setUserData] = useState<UserData | null>(null);
  const [activityStats, setActivityStats] = useState<ActivityStats | null>(null);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([]);
  const [aiSummary, setAiSummary] = useState<AIAssistantSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const { token, user: authUser, logout } = useAuth() 
  const navigate = useNavigate()

  useEffect(() => {
    if (token) {
    fetchUserData();
    } else {
      setError("Please log in to view your profile")
      setLoading(false)
    }
  }, [token]);

  const fetchUserData = async () => {
    try {
      setLoading(true);
      setError(null);

     const headers = {
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
     }


      const [
        userResponse,
        statsResponse,
        notificationsResponse,
        activityResponse,
        // aiSummaryResponse
      ] = await Promise.all([
        axios.get(`${API}/user/profile`, { headers }),
        axios.get(`${API}/user/activity-stats`, { headers }),
        axios.get(`${API}/user/notifications`, { headers }),
        axios.get(`${API}/user/recent-activity`, { headers }),
        // axios.get(`${API}/user/ai-summary`, { headers })
      ]);

      setUserData(userResponse.data);
      setActivityStats(statsResponse.data);
      setNotifications(notificationsResponse.data);
      setRecentActivity(activityResponse.data);
      // setAiSummary(aiSummaryResponse.data);

    } catch (err: any) {
      console.error('Error fetching user data:', err);

      if (err.response?.status === 401) {
        setError("Session expired. Plese log in again.")
        logout()
        return
      }

      setError("Failed to load profile data. Please try again")
    } finally {
      setLoading(false);
    }
  };
  
  const handleLogout = () => {
    logout()
  } 

  const handleUpdateProfile = () => {
    // Navigate to profile update page or open modal
    console.log('Navigate to update profile');
  };

  const handleChangePassword = () => {
    navigate("/password-reset")
    console.log('Navigate to change password');
  };

  const handleViewDocuments = () => {
    // Navigate to documents page
    navigate('/documents/');
  };

  

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  const getRelativeTime = (dateString: string) => {
    const now = new Date();
    const date = new Date(dateString);
    const diffInMs = now.getTime() - date.getTime();
    const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
    const diffInDays = Math.floor(diffInHours / 24);

    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours} hours ago`;
    if (diffInDays === 1) return '1 day ago';
    return `${diffInDays} days ago`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-4">{error}</div>
          <button 
            onClick={fetchUserData}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
  <div className="flex flex-col md:flex-row bg-gray-50 min-h-screen">
    {/* Profile Image Section */}
    <ProfileImageUpload />

    {/* Main Content Area */}
    <div className="flex-1 p-4 sm:p-6 md:p-8 space-y-6">
      
      {/* User Profile Summary Panel */}
      <div className="bg-white rounded-lg shadow-sm p-4 sm:p-6 border border-gray-200">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-800 mb-4 flex items-center">
          <User className="mr-3 text-blue-600" size={24} />
          User Profile Summary
        </h2>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center">
            <span className="font-semibold text-gray-600 w-full sm:w-24">Name:</span>
            <span className="text-gray-800">{userData?.name || (authUser as any)?.name || 'Loading...'}</span>
          </div>
          <div className="flex flex-col sm:flex-row items-start sm:items-center">
            <span className="font-semibold text-gray-600 w-full sm:w-24">Role:</span>
            <span className="text-gray-800">{userData?.role || authUser?.roles?.[0] || 'Loading...'}</span>
          </div>
          <div className="flex flex-col sm:flex-row items-start sm:items-center">
            <Mail className="mr-2 text-gray-500" size={16} />
            <span className="font-semibold text-gray-600 w-full sm:w-20">Email:</span>
            <span className="text-gray-800">{userData?.email || authUser?.email || 'Loading...'}</span>
          </div>
          <div className="flex flex-col sm:flex-row items-start sm:items-center">
            <Calendar className="mr-2 text-gray-500" size={16} />
            <span className="font-semibold text-gray-600 w-full sm:w-20">Last Login:</span>
            <span className="text-gray-800">{userData?.lastLogin ? formatDate(userData.lastLogin) : 'Loading...'}</span>
          </div>
        </div>
      </div>

      {/* Quick Activity Stats */}
      <div className="bg-white rounded-lg shadow-sm p-4 sm:p-6 border border-gray-200">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-800 mb-4 flex items-center">
          <Activity className="mr-3 text-green-600" size={24} />
          Quick Activity Stats
        </h2>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6">
          <div className="text-center p-4 bg-blue-50 rounded-lg">
            <FileText className="mx-auto mb-2 text-blue-600" size={32} />
            <div className="text-2xl font-bold text-blue-600">{activityStats?.documentsUploaded || 0}</div>
            <div className="text-gray-600">Documents uploaded</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <FileText className="mx-auto mb-2 text-green-600" size={32} />
            <div className="text-2xl font-bold text-green-600">{activityStats?.contractsAnalyzed || 0}</div>
            <div className="text-gray-600">Contracts analyzed</div>
          </div>
          <div className="text-center p-4 bg-purple-50 rounded-lg">
            <MessageSquare className="mx-auto mb-2 text-purple-600" size={32} />
            <div className="text-2xl font-bold text-purple-600">{activityStats?.questionsAnswered || 0}</div>
            <div className="text-gray-600">Questions answered</div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="bg-white rounded-lg shadow-sm p-4 sm:p-6 border border-gray-200">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-800 mb-4">Quick Actions</h2>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
          <button 
            onClick={handleUpdateProfile}
            className="flex items-center justify-center p-4 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors border border-blue-200"
          >
            <RotateCcw className="mr-2 text-blue-600" size={20} />
            <span className="text-blue-700 font-medium">Update Profile</span>
          </button>
          <button 
            onClick={handleChangePassword}
            className="flex items-center justify-center p-4 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
          >
            <Lock className="mr-2 text-gray-600" size={20} />
            <span className="text-gray-700 font-medium">Change Password</span>
          </button>
          <button 
            onClick={handleViewDocuments}
            className="flex items-center justify-center p-4 bg-green-50 hover:bg-green-100 rounded-lg transition-colors border border-green-200"
          >
            <Folder className="mr-2 text-green-600" size={20} />
            <span className="text-green-700 font-medium">View Documents</span>
          </button>
          <button 
            onClick={handleLogout}
            className="flex items-center justify-center p-4 bg-red-50 hover:bg-red-100 rounded-lg transition-colors border border-red-200"
          >
            <LogOut className="mr-2 text-red-600" size={20} />
            <span className="text-red-700 font-medium">Logout</span>
          </button>
        </div>
      </div>

      {/* Notifications & Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Notifications */}
        <div className="bg-white rounded-lg shadow-sm p-4 sm:p-6 border border-gray-200">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            <Bell className="mr-2 text-orange-600" size={20} />
            Notifications
          </h3>
          <div className="space-y-3">
            {notifications.length > 0 ? (
              notifications.map((notification) => (
                <div key={notification.id} className={`p-3 border-l-4 rounded ${
                  notification.type === 'warning' ? 'bg-orange-50 border-orange-400' :
                  notification.type === 'success' ? 'bg-green-50 border-green-400' :
                  'bg-blue-50 border-blue-400'
                }`}>
                  <p className={`${
                    notification.type === 'warning' ? 'text-orange-800' :
                    notification.type === 'success' ? 'text-green-800' :
                    'text-blue-800'
                  }`}>{notification.message}</p>
                  <p className="text-xs text-gray-500 mt-1">{getRelativeTime(notification.createdAt)}</p>
                </div>
              ))
            ) : (
              <div className="text-gray-500 text-center py-4">No notifications</div>
            )}
          </div>
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow-sm p-4 sm:p-6 border border-gray-200">
          <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
            <Activity className="mr-2 text-blue-600" size={20} />
            Recent Activity
          </h3>
          <div className="space-y-3">
            {recentActivity.length > 0 ? (
              recentActivity.map((activity) => (
                <div key={activity.id} className="p-3 bg-gray-50 rounded border">
                  <p className="text-gray-800">
                    <span className="font-medium">{activity.action}</span> {activity.fileName}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">{getRelativeTime(activity.timestamp)}</p>
                </div>
              ))
            ) : (
              <div className="text-gray-500 text-center py-4">No recent activity</div>
            )}
          </div>
        </div>
      </div>

      {/* AI Assistant Summary */}
      <div className="bg-white rounded-lg shadow-sm p-4 sm:p-6 border border-gray-200">
        <h3 className="text-lg font-bold text-gray-800 mb-4 flex items-center">
          <HelpCircle className="mr-2 text-indigo-600" size={20} />
          AI Assistant Summary
        </h3>
        <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
          {aiSummary ? (
            <p className="text-indigo-800">
              You asked {aiSummary.weeklyQuestions} questions this week and uploaded {aiSummary.documentsThisWeek} new documents for analysis. 
              Your most active day was {aiSummary.mostActiveDay} with {aiSummary.contractReviews} contract reviews completed.
            </p>
          ) : (
            <p className="text-indigo-800">Loading AI assistant summary...</p>
          )}
        </div>
      </div>

    </div>
  </div>
);
}

export default UserProfile