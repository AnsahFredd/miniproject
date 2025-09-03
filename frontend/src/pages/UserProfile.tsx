import React, { useState, useEffect, useMemo } from 'react';
import { User, Mail, Calendar, FileText, MessageSquare, HelpCircle, RotateCcw, Lock, Folder, LogOut, Bell, Activity } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../auth/AuthContext';
import  { useNavigate } from "react-router-dom"
import { motion } from 'framer-motion';

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

// Animation variants
const pageVariants = useMemo(() => ({
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.06 } }
}), []);
const cardVariants = useMemo(() => ({
  hidden: { opacity: 0, y: 12 },
  show: { opacity: 1, y: 0, transition: { duration: 0.35 } }
}), []);
const itemVariants = useMemo(() => ({
  hidden: { opacity: 0, y: 6 },
  show: { opacity: 1, y: 0, transition: { duration: 0.25 } }
}), []);

useEffect(() => {
  if (token) {
    fetchUserData();
  } else {
    setError("Please log in to view your profile");
    setLoading(false);
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
      aiSummaryResponse
    ] = await Promise.all([
      axios.get(`${API}/user/profile`, { headers }),
      axios.get(`${API}/user/activity-stats`, { headers }),
      axios.get(`${API}/user/notifications`, { headers }),
      axios.get(`${API}/user/recent-activity`, { headers }),
      axios.get(`${API}/user/ai-summary`, { headers }),
    ]);

    setUserData(userResponse.data);
    setActivityStats(statsResponse.data);
    setNotifications(notificationsResponse.data);
    setRecentActivity(activityResponse.data);
    setAiSummary(aiSummaryResponse.data);
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
  console.log('Navigate to update profile');
};

const handleChangePassword = () => {
  navigate("/password-reset")
};

const handleViewDocuments = () => {
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
    <div className="flex items-center justify-center min-h-screen bg-[var(--bg-soft)]" role="status" aria-live="polite">
      <div className="animate-spin rounded-full h-24 w-24 border-4 border-[color:rgb(20_184_166_/_26%)] border-t-[var(--color-accent)]"></div>
    </div>
  );
}

if (error) {
  return (
    <div className="flex items-center justify-center min-h-screen bg-[var(--bg-soft)]">
      <div className="text-center">
        <div className="text-[var(--color-primary)] text-xl mb-4">{error}</div>
        <button 
          onClick={fetchUserData}
          className="btn btn-primary"
        >
          Retry
        </button>
      </div>
    </div>
  );
}

// Helper for notification colors within the 3-color scheme
const getNoticeClasses = (type: Notification['type']) => {
  switch (type) {
    case 'success':
      return 'bg-[color:rgb(20_184_166_/_10%)] border-[color:rgb(20_184_166_/_26%)] text-[var(--color-primary)]';
    case 'warning':
      return 'bg-[color:rgb(15_23_42_/_6%)] border-[color:rgb(15_23_42_/_16%)] text-[var(--color-primary)]';
    default: // info
      return 'bg-[var(--bg-soft)] border-gray-200 text-[var(--color-primary)]';
  }
};

return (
  <div className="relative bg-[var(--bg-soft)] min-h-screen">
    <div className="pointer-events-none absolute -z-10 inset-0 overflow-hidden">
      <div className="absolute -top-24 -left-24 w-72 h-72 rounded-full bg-[color:rgb(20_184_166_/_10%)] blur-3xl"></div>
      <div className="absolute -bottom-32 -right-24 w-96 h-96 rounded-full bg-[color:rgb(15_23_42_/_6%)] blur-3xl"></div>
    </div>

    <motion.div
      className="flex flex-col md:flex-row max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 gap-6"
      variants={pageVariants}
      initial="hidden"
      animate="show"
    >
      <div className="flex-1 space-y-6">
        
        {/* User Profile Summary Panel */}
        <motion.div variants={cardVariants} className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <h2 className="text-2xl font-bold text-[var(--color-primary)] mb-4 flex items-center">
            <User className="mr-3 text-[var(--color-accent)]" size={24} />
            User Profile Summary
          </h2>
          
          <motion.div
            className="grid grid-cols-1 sm:grid-cols-2 gap-4"
            variants={pageVariants}
            initial="hidden"
            animate="show"
          >
            <motion.div variants={itemVariants} className="flex flex-col sm:flex-row items-start sm:items-center">
              <span className="font-semibold text-[var(--color-secondary)] w-full sm:w-24">Name:</span>
              <span className="text-[var(--color-primary)]">{userData?.name || (authUser as any)?.name || 'Loading...'}</span>
            </motion.div>
            <motion.div variants={itemVariants} className="flex flex-col sm:flex-row items-start sm:items-center">
              <span className="font-semibold text-[var(--color-secondary)] w-full sm:w-24">Role:</span>
              <span className="text-[var(--color-primary)]">{userData?.role || authUser?.roles?.[0] || 'Loading...'}</span>
            </motion.div>
            <motion.div variants={itemVariants} className="flex flex-col sm:flex-row items-start sm:items-center">
              <Mail className="mr-2 text-[var(--color-secondary)]" size={16} />
              <span className="font-semibold text-[var(--color-secondary)] w-full sm:w-20">Email:</span>
              <span className="text-[var(--color-primary)]">{userData?.email || authUser?.email || 'Loading...'}</span>
            </motion.div>
            <motion.div variants={itemVariants} className="flex flex-col sm:flex-row items-start sm:items-center">
              <Calendar className="mr-2 text-[var(--color-secondary)]" size={16} />
              <span className="font-semibold text-[var(--color-secondary)] w-full sm:w-28">Last Login:</span>
              <span className="text-[var(--color-primary)]">{userData?.lastLogin ? formatDate(userData.lastLogin) : 'Loading...'}</span>
            </motion.div>
          </motion.div>
        </motion.div>

        {/* Quick Activity Stats */}
        <motion.div variants={cardVariants} className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <h2 className="text-2xl font-bold text-[var(--color-primary)] mb-4 flex items-center">
            <Activity className="mr-3 text-[var(--color-accent)]" size={24} />
            Quick Activity Stats
          </h2>
          
          <motion.div
            className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4"
            variants={pageVariants}
            initial="hidden"
            animate="show"
          >
            <motion.div
              variants={itemVariants}
              whileHover={{ y: -2, scale: 1.02 }}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
              className="text-center p-5 rounded-lg border border-[color:rgb(20_184_166_/_26%)] bg-[color:rgb(20_184_166_/_8%)]"
            >
              <FileText className="mx-auto mb-2 text-[var(--color-accent)]" size={28} />
              <div className="text-2xl font-bold text-[var(--color-accent)]">{activityStats?.documentsUploaded || 0}</div>
              <div className="text-[var(--color-secondary)]">Documents uploaded</div>
            </motion.div>
            <motion.div
              variants={itemVariants}
              whileHover={{ y: -2, scale: 1.02 }}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
              className="text-center p-5 rounded-lg border border-gray-200 bg-[var(--bg-soft)]"
            >
              <FileText className="mx-auto mb-2 text-[var(--color-primary)]" size={28} />
              <div className="text-2xl font-bold text-[var(--color-primary)]">{activityStats?.contractsAnalyzed || 0}</div>
              <div className="text-[var(--color-secondary)]">Contracts analyzed</div>
            </motion.div>
            <motion.div
              variants={itemVariants}
              whileHover={{ y: -2, scale: 1.02 }}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
              className="text-center p-5 rounded-lg border border-gray-200 bg-white"
            >
              <MessageSquare className="mx-auto mb-2 text-[var(--color-secondary)]" size={28} />
              <div className="text-2xl font-bold text-[var(--color-secondary)]">{activityStats?.questionsAnswered || 0}</div>
              <div className="text-[var(--color-secondary)]">Questions answered</div>
            </motion.div>
          </motion.div>
        </motion.div>

        {/* Action Buttons */}
        <motion.div variants={cardVariants} className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <h2 className="text-2xl font-bold text-[var(--color-primary)] mb-4">Quick Actions</h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            <motion.button 
              onClick={handleUpdateProfile}
              whileHover={{ y: -2, scale: 1.02 }}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
              className="flex items-center justify-center p-4 bg-[var(--bg-soft)] hover:bg-[color:rgb(20_184_166_/_10%)] rounded-lg transition-colors border border-gray-200"
            >
              <RotateCcw className="mr-2 text-[var(--color-accent)]" size={20} />
              <span className="text-[var(--color-primary)] font-medium">Update Profile</span>
            </motion.button>
            <motion.button 
              onClick={handleChangePassword}
              whileHover={{ y: -2, scale: 1.02 }}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
              className="flex items-center justify-center p-4 bg-white hover:bg-[var(--bg-soft)] rounded-lg transition-colors border border-gray-200"
            >
              <Lock className="mr-2 text-[var(--color-secondary)]" size={20} />
              <span className="text-[var(--color-primary)] font-medium">Change Password</span>
            </motion.button>
            <motion.button 
              onClick={handleViewDocuments}
              whileHover={{ y: -2, scale: 1.02 }}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
              className="flex items-center justify-center p-4 bg-white hover:bg-[var(--bg-soft)] rounded-lg transition-colors border border-gray-200"
            >
              <Folder className="mr-2 text-[var(--color-secondary)]" size={20} />
              <span className="text-[var(--color-primary)] font-medium">View Documents</span>
            </motion.button>
            <motion.button 
              onClick={handleLogout}
              whileHover={{ y: -2, scale: 1.02 }}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
              className="flex items-center justify-center p-4 bg-white hover:bg-[var(--bg-soft)] rounded-lg transition-colors border border-gray-200"
            >
              <LogOut className="mr-2 text-[var(--color-primary)]" size={20} />
              <span className="text-[var(--color-primary)] font-medium">Logout</span>
            </motion.button>
          </div>
        </motion.div>

        {/* Notifications & Activity */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Notifications */}
          <motion.div variants={cardVariants} className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <h3 className="text-lg font-bold text-[var(--color-primary)] mb-4 flex items-center">
              <Bell className="mr-2 text-[var(--color-accent)]" size={20} />
              Notifications
            </h3>
            <motion.div
              className="space-y-3"
              variants={pageVariants}
              initial="hidden"
              animate="show"
            >
              {notifications.length > 0 ? (
                notifications.map((notification) => (
                  <motion.div
                    key={notification.id}
                    variants={itemVariants}
                    className={`p-3 border rounded ${getNoticeClasses(notification.type)}`}
                  >
                    <p className="text-sm">{notification.message}</p>
                    <p className="text-xs text-[var(--color-secondary)] mt-1">{getRelativeTime(notification.createdAt)}</p>
                  </motion.div>
                ))
              ) : (
                <div className="text-[var(--color-secondary)] text-center py-4">No notifications</div>
              )}
            </motion.div>
          </motion.div>

          {/* Recent Activity */}
          <motion.div variants={cardVariants} className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
            <h3 className="text-lg font-bold text-[var(--color-primary)] mb-4 flex items-center">
              <Activity className="mr-2 text-[var(--color-accent)]" size={20} />
              Recent Activity
            </h3>
            <motion.div
              className="space-y-3"
              variants={pageVariants}
              initial="hidden"
              animate="show"
            >
              {recentActivity.length > 0 ? (
                recentActivity.map((activity) => (
                  <motion.div
                    key={activity.id}
                    variants={itemVariants}
                    whileHover={{ y: -1 }}
                    className="p-3 bg-[var(--bg-soft)] rounded border border-gray-200"
                  >
                    <p className="text-[var(--color-primary)]">
                      <span className="font-medium">{activity.action}</span> {activity.fileName}
                    </p>
                    <p className="text-sm text-[var(--color-secondary)] mt-1">{getRelativeTime(activity.timestamp)}</p>
                  </motion.div>
                ))
              ) : (
                <div className="text-[var(--color-secondary)] text-center py-4">No recent activity</div>
              )}
            </motion.div>
          </motion.div>
        </div>

        {/* AI Assistant Summary */}
        <motion.div variants={cardVariants} className="bg-white rounded-xl shadow-sm p-6 border border-gray-200">
          <h3 className="text-lg font-bold text-[var(--color-primary)] mb-4 flex items-center">
            <HelpCircle className="mr-2 text-[var(--color-accent)]" size={20} />
            AI Assistant Summary
          </h3>
          <div className="bg-[color:rgb(20_184_166_/_10%)] p-4 rounded-lg border border-[color:rgb(20_184_166_/_26%)]">
            {aiSummary ? (
              <p className="text-[var(--color-primary)]">
                You asked {aiSummary.weeklyQuestions} questions this week and uploaded {aiSummary.documentsThisWeek} new documents for analysis. 
                Your most active day was {aiSummary.mostActiveDay} with {aiSummary.contractReviews} contract reviews completed.
              </p>
            ) : (
              <p className="text-[var(--color-secondary)]">Loading AI assistant summary...</p>
            )}
          </div>
        </motion.div>
      </div>
    </motion.div>
  </div>
);
}

export default UserProfile;
