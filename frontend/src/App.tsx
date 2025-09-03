import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Signup from "./auth/Signup";
import Login from "./auth/Login";
import ForgotPassword from "./auth/ForgotPassword";
import LandingPage from "./pages/LandingPage";
import Layout from "./components/Layout";
import HomePage from "./pages/HomePage";
import Documents from "./pages/Documents";
import DocumentReview from "./pages/DocumentReview";
import SearchPage from "./pages/Search";
import UserProfile from "./pages/UserProfile";
import NewsFeed from "./pages/NewsFeed"
import ProtectedRoute from "./routes/ProtectedRoutes";
import PublicOnlyRoute from "./routes/PublicOnlyRoutes";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { useAnalytics } from "./hooks/useAnalytics";
import ConfirmEmail from "./pages/ConfirmEmail";
import CheckEmailPage from "./pages/CheckEmail";
import ResetPassword from "./pages/ResetPaaword";
import DemoPage from "./pages/DemoPage";
const App: React.FC = () => {
  useAnalytics(); // Initialize analytics tracking

  return (
    <ErrorBoundary>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<LandingPage />} />
          <Route path="/demo" element={<DemoPage />} />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<HomePage />} />
            <Route path="/document" element={<Documents />} />
            <Route path="/document/:id/review" element={<DocumentReview />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/profile" element={<UserProfile />} />
            <Route path="/news" element={<NewsFeed />}/>
          </Route>

          <Route path="/change-password" element={<ResetPassword />} />

          {/* Role-based Routes Example */}
          <Route element={<ProtectedRoute requiredRoles={['manager', 'admin']} />}>
            <Route path="/reports" element={<div>Reports Page</div>} />
          </Route>

          {/* Permission-based Routes Example */}
          <Route element={<ProtectedRoute requiredPermissions={['document.delete']} />}>
            <Route path="/document/:id/delete" element={<div>Delete Document</div>} />
          </Route>

          {/* Public Only Routes */}
          <Route
            path="/signup"
            element={
              <PublicOnlyRoute>
                <Signup />
              </PublicOnlyRoute>
            }
          />
          <Route
            path="/login"
            element={
              <PublicOnlyRoute>
                <Login />
              </PublicOnlyRoute>
            }
          />
          <Route
            path="/reset-password"
            element={
              <PublicOnlyRoute>
                <ForgotPassword />
              </PublicOnlyRoute>
            }
          />
          <Route 
          path="/confirm-email"
          element={
            <PublicOnlyRoute>
             <ConfirmEmail />
            </PublicOnlyRoute>
          }
          />

          <Route path="/check-email"
          element={
            <PublicOnlyRoute>
              <CheckEmailPage />
            </PublicOnlyRoute>
          }
          />
      

          {/* Catch-all route */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </ErrorBoundary>
  );
};

export default App;