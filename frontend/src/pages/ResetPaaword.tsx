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
  const { resetPassword } = useAuth();
  const navigate = useNavigate();
  const hasValidated = useRef<boolean>(false);

  useEffect(() => {
    const checkToken = async () => {
      if (!token) {
        navigate("/forgot-password?error=missing_token");
        return;
      }

      if (hasValidated.current) {
        return;
      }

      hasValidated.current = true;
      setIsLoading(true);
      
      try {
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
      } finally {
        setIsLoading(false);
      }
    };

    checkToken();
  }, []); // only run once

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

  if (tokenValid === null) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-[var(--bg-soft)]" role="status" aria-live="polite">
        <div className="bg-white p-8 rounded-lg shadow-md">
          <h2 className="text-2xl font-bold text-[var(--color-primary)] mb-4">Reset Password</h2>
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[var(--color-accent)] mx-auto mb-4"></div>
            <p className="text-[var(--color-secondary)]">Validating token...</p>
          </div>
        </div>
      </div>
    );
  }

  if (tokenValid === false) {
    return (
      <div className="flex flex-col items-center justify-center mt-12 gap-4">
        <h1 className="text-2xl font-bold text-[var(--color-primary)]">Reset Password</h1>
        <p className="text-red-600" role="alert" aria-live="assertive">{error}</p>
        <button
          onClick={() => navigate("/forgot-password")}
          className="btn btn-secondary"
        >
          Request New Reset Link
        </button>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-[var(--bg-soft)]">
      <form onSubmit={handleReset} className="bg-white p-8 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold text-[var(--color-primary)] mb-6">Reset Your Password</h2>
        
        <input
          type="password"
          placeholder="New Password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
          className="input w-80 mb-4 block"
          required
          minLength={8}
        />
        
        <input
          type="password"
          placeholder="Confirm Password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          className="input w-80 mb-4 block"
          required
        />
        
        {error && <div className="text-red-600 mb-4" role="alert" aria-live="assertive">{error}</div>}
        
        <button
          type="submit"
          disabled={isLoading}
          className="btn btn-primary w-full disabled:opacity-50"
        >
          {isLoading ? "Resetting..." : "Reset Password"}
        </button>
      </form>
    </div>
  );
};

export default ResetPassword;
