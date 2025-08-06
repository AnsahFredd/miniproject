import React, { useState, useEffect, useRef } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import axios from "axios";
import { useAuth } from "../auth/AuthContext";

const API = import.meta.env.VITE_API_BASE_URL;

const ResetPassword: React.FC = () => {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const [newPassword, setNewPassword] = useState<string>("");
  const [confirmPassword, setConfirmPassword] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [tokenValid, setTokenValid] = useState<boolean | null>(null);
  const { resetPassword } = useAuth(); // Remove validateResetToken from here
  const navigate = useNavigate();
  const hasValidated = useRef<boolean>(false);

  // Validate token on component mount
  useEffect(() => {
    const checkToken = async () => {
      // Early return if no token
      if (!token) {
        navigate("/forgot-password?error=missing_token");
        return;
      }

      // Prevent multiple validation calls
      if (hasValidated.current) {
        return;
      }

      hasValidated.current = true;
      setIsLoading(true);
      
      try {
        console.log("Making token validation request...");
        // Direct API call - no global state interference
        const response = await axios.get(
          `${API}/auth/verify-reset-token/${encodeURIComponent(token)}`,
          { withCredentials: true }
        );
        
        const isValid = response.data.valid;
        setTokenValid(isValid);

        if (!isValid) {
          setError("Invalid or expired token. Please request a new reset link.");
        }
      } catch (err) {
        setError("Failed to validate token. Please try again.");
        setTokenValid(false);
        console.error("Token validation error:", err);
      } finally {
        setIsLoading(false);
      }
    };

    checkToken();
  }, []); // EMPTY dependency array - only run once on mount

  const handleReset = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    if (!newPassword || newPassword.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("Passwords don't match.");
      return;
    }

    setIsLoading(true);
    setError("");
    
    try {
      await resetPassword(token!, newPassword);
      navigate("/login?message=password_reset_success");
    } catch (error) {
      let errorMessage = "Error resetting password";
      if (axios.isAxiosError(error)) {
        errorMessage = error.response?.data?.detail || errorMessage;
      }
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  // Show loading state while checking token
  if (tokenValid === null) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="bg-white p-8 rounded-lg shadow-md">
          <h2 className="text-2xl font-bold mb-4">Reset Password</h2>
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
            <p>Validating token...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state for invalid token
  if (tokenValid === false) {
    return (
      <div className="flex flex-col items-center justify-center mt-12 gap-4">
        <h1 className="text-2xl font-bold">Reset Password</h1>
        <p className="text-red-500">{error}</p>
        <button
          onClick={() => navigate("/forgot-password")}
          className="bg-black text-white px-6 py-2 rounded"
        >
          Request New Reset Link
        </button>
      </div>
    );
  }

  // Show password reset form for valid token
  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-50">
      <form onSubmit={handleReset} className="bg-white p-8 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold mb-6">Reset Your Password</h2>
        
        <input
          type="password"
          placeholder="New Password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          className="border px-4 py-2 rounded w-80 mb-4 block"
          required
          minLength={8}
        />
        
        <input
          type="password"
          placeholder="Confirm Password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          className="border px-4 py-2 rounded w-80 mb-4 block"
          required
        />
        
        {error && <div className="text-red-600 mb-4">{error}</div>}
        
        <button
          type="submit"
          disabled={isLoading}
          className="bg-blue-500 text-white px-6 py-2 rounded w-full disabled:bg-gray-400"
        >
          {isLoading ? "Resetting..." : "Reset Password"}
        </button>
      </form>
    </div>
  );
};

export default ResetPassword;