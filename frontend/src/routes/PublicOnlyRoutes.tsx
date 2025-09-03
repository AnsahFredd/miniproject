import React from "react";
import { Navigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import {ErrorBoundary} from "../components/ErrorBoundary"
import {useAnalytics} from "../hooks/useAnalytics"

interface PublicOnlyRouteProps {
  children: React.ReactNode;
  redirectTo?: string | false
}

const PublicOnlyRoute: React.FC<PublicOnlyRouteProps> = ({
  children,
  redirectTo = "/dashboard"
}) => {
  const { token, error,loading } = useAuth()
  const analytics = useAnalytics()

  if (loading) {
    return <LoadingSkeleton type="auth" />
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
          <h3 className="text-lg font-medium text-red-900 mb-2">
            Authentication Error
          </h3>
          <p className="text-sm text-red-700">{error}</p>
        </div>
      </div>
    )
  }

  if (token) {

    console.log("User is authenticated");
  console.log("redirectTo:", redirectTo);


    if (redirectTo === false) {
      console.log("No redirect; showing children");

      return (
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      )
    }

    if (typeof redirectTo === "string") {
    analytics.track('public_route_redirect', {
      from: window.location.pathname,
      to: redirectTo,
      reason: 'alredy authenticated'
    })
    return <Navigate to={redirectTo} replace/>
  }
  }

  return (
    <ErrorBoundary>
      {children}
    </ErrorBoundary>
  )
}


export default PublicOnlyRoute
