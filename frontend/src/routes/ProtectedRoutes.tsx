import React from "react";
import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { useAnalytics } from "../hooks/useAnalytics";

interface ProtectedRouteProps {
  requiredRoles?: string[];
  requiredPermissions?: string[];
  fallbackPath?: string
}


const ProtectRouted: React.FC<ProtectedRouteProps> = ({
  requiredRoles = [],requiredPermissions = [], fallbackPath = "/login"
}) => {

  const { token, user, loading, error, hasRole, hasPermission} = useAuth()
  const analytics = useAnalytics()

  if (loading) {
    return <LoadingSkeleton type="page"/>
  }

  if (error) {
    return (
       <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
          <h3 className="text-lg font-medium text-red-900 mb-2">Authentication Error</h3>
          <p className="text-sm text-red-700 mb-4">{error}</p>
          <Navigate to={fallbackPath} replace />
        </div>
      </div>
    )
  }

  if (!token) {
    analytics.track('protected_route_redirect', {
      from: window.location.pathname,
      to: fallbackPath,
      reason: "not_authenticated"
    })
    return <Navigate to={fallbackPath} replace />
  }

  // Role-based access control
  if (requiredRoles.length > 0) {
    const hasRequiredRole = requiredRoles.some(role => hasRole(role))
    if (!hasRequiredRole) {
      analytics.track('access_denied', {
        route: window.location.pathname,
        reason: 'insufficient_roles',
        requiredRoles,
        userRoles: user?.roles
      });

      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <h3 className="text-lg font-medium text-red-900 mb-2">Access Denied</h3>
            <p className="text-sm text-red-700">You don't have permission to access this page.</p>
          </div>
        </div>
      )
    }
  }

  // Permission-based access control
  if (requiredPermissions.length > 0) {
    const hasRequiredPermission = requiredPermissions.some(permission => hasPermission(permission));
    if (!hasRequiredPermission) {
      analytics.track('access_denied', {
        route: window.location.pathname,
        reason: 'insufficient_permissions',
        requiredPermissions,
        userPermissions: user?.permission
      })

      return (
         <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
            <h3 className="text-lg font-medium text-red-900 mb-2">Access Denied</h3>
            <p className="text-sm text-red-700">You don't have the required permissions to access this page.</p>
          </div>
        </div>
      )
    }
  }

  return (
    <ErrorBoundary>
      <Outlet />
    </ErrorBoundary>
  )
}


export default ProtectRouted
